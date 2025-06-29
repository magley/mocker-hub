import asyncio
from sqlmodel import Session
from rq import get_current_job
from app.api.config.database import get_database
from app.api.config.initialize import init_registry_client
from app.api.events.event_model import EventLevel

class JobsService:

    # NOTE: Other services should not be added
    # as they will create circular dependencies,
    # and jobs are run in function scope.
    # All required services should be defined
    # within the function itself.

    def _get_session(self) -> Session:
        return next(get_database())

    def _get_event_loop(self) -> asyncio.AbstractEventLoop:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop

    def _get_current_job_metadata(self) -> dict:
        job = get_current_job()
        return {
            "id": job.id if job else "unknown",
            "origin": job.origin if job else "unknown",
            "retries_left": job.retries_left if job else "unknown"
        }

    def delete_tag_job(self, username:str, repo_id: int, tag_name: str):
        from app.api.registry.registry_service import RegistryService
        session = self._get_session()
        loop = self._get_event_loop()
        client = init_registry_client()
        registry_service = RegistryService(session)

        try:
            repo = registry_service.repo_service.find_by_id(repo_id)
            tag = registry_service.tag_service.find_by_name_and_repo_id(tag_name, repo_id)

        except Exception:
            registry_service.event_service.log(EventLevel.Info, f"Tag '{tag_name}' has already been deleted by another job.")
            return

        try:
            response = loop.run_until_complete(registry_service.delete_tag(client, username, repo, tag))
            registry_service.event_service.log(EventLevel.Info, response.message)

        except Exception:
            job_info = self._get_current_job_metadata()

            registry_service.event_service.log(
                EventLevel.Error, 
                (
                    f"Tag '{tag.name}' is not deleted (job_id={job_info['id']}, retries_left={job_info['retries_left']}, queue={job_info['origin']}). " 
                    f"ADMIN: For an immediate response, check both the queue dashboard and the log trace."
                )
            )
            raise
        
        finally:
            loop.close()
            session.close()

def get_team_service() -> JobsService:
    return JobsService()