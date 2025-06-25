import asyncio

from rq import get_current_job
from app.api.config.database import get_database
from app.api.config.initialize import init_registry_client
from app.api.events.event_model import EventLevel

def delete_tag_job(username:str, repo_id: int, tag_name: str):
    from app.api.registry.registry_service import RegistryService
    
    client = init_registry_client()

    with next(get_database()) as session:
        registry_service = RegistryService(session)
        try:
            repo = registry_service.repo_service.find_by_id(repo_id)
            tag = registry_service.tag_service.find_by_name_and_repo_id(tag_name, repo_id)
        except Exception:
            registry_service.event_service.log(EventLevel.Info, f"Tag '{tag_name}' has already been deleted by another job.")
            return

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            response = loop.run_until_complete(registry_service.delete_tag(client, username, repo, tag))
            registry_service.event_service.log(EventLevel.Info, response.message)

        except Exception:
            job = get_current_job()
            job_id = job.id if job else "unknown"
            origin = job.origin if job else "unknown"
            retries_left = job.retries_left if job else "unknown"

            registry_service.event_service.log(
                EventLevel.Error, 
                (
                    f"Tag '{tag.name}' is not deleted (job_id={job_id}, retries_left={retries_left}, queue={origin}). " 
                    f"ADMIN: For an immediate response, check both the queue dashboard and the log trace."
                )
            )
            raise
        
        finally:
            loop.close()