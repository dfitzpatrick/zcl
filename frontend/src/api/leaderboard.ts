import axios from 'axios'
import { filteredEndpoint, IPagedResult } from './apiCommon'

export interface ILeaderboardFilters {
    [key: string]: string|number|null|undefined
    mode?: string
    limit: number
    offset: number
    name?: string
    sort?: string,
    profile_id?: string
}
export interface ILeaderboardResult {
    id: number,
    mode: string,
    name: string,
    rank: number,
    created: string,
    updated: string,
    games: number,
    wins: number,
    losses: number,
    elo: string,
    win_rate: string,
    profile: {
        id: string,
        created: string,
        name: string,
        profile_url: string
        avatar_url: string
    }
}
export interface ILeaderboardQuery {
    count: number,
    next: string,
    previous: string,
    results: ILeaderboardResult[]
}

export async function fetchLeaderboards(): Promise<ILeaderboardResult[]>
export async function fetchLeaderboards(f: ILeaderboardFilters): Promise<IPagedResult<ILeaderboardResult>>
export async function fetchLeaderboards(f?: ILeaderboardFilters): Promise<ILeaderboardResult[]|IPagedResult<ILeaderboardResult>> {
    const url = filteredEndpoint<ILeaderboardFilters>('/api/leaderboards/', f)
    const result = await axios.get(url)
    return result.data
}
 
export default fetchLeaderboards