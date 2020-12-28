import axios from 'axios'
interface IndexedObject {
    [key: string]: string | number | null | undefined
}
export interface IPagingFilters {
    offset: number,
    limit: number
}
export interface IPagedResult<T> {
    count: number,
    next: string,
    previous: string,
    results: T[]

}
export async function fetchAll<T>(endpoint: string): Promise<T[]> {
    const result = await axios.get(endpoint)
    return result.data
}
export function filteredEndpoint<T extends IndexedObject>(endpoint: string, filters?: T) {
    /// Derive query params from the type
    //Key value pairs
    if (filters == undefined) {
        return endpoint
    }
    const qs =(
        Object.keys(filters)
        .map((key) => {
            const value = filters[key]
            if (value == null || value == undefined) { return '' }
            return `${key}=${value}`
        })
    )
    return `${endpoint}?${qs.join('&')}`
}   