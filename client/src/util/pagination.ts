export class PaginationParams {
    constructor(
        public page: number,
        public limit: number,
        public sort_by: string | null,
        public sort_order: string | null
    ) {}

    toQueryParams(): URLSearchParams {
        const queryParams = new URLSearchParams({
            page: String(this.page),
            limit: String(this.limit),
            sort_by: this.sort_by || '',
            sort_order: this.sort_order || '',
        });
        return queryParams;
    }
}

export interface PaginationDTO<T> {
    items: T[],
    total_count: number,
}