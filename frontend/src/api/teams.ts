import axios from 'axios'
import { filteredEndpoint, IPagedResult } from './apiCommon'
export interface IProfileResult {
    id: string,
    created: string,
    name: string,
    profile_url: string,
    avatar_url: string
}
export interface ITeamResult {
    id: number,
    profiles: IProfileResult[],
    team_elo: string,
    games: number,
    wins: number,
    losses: number,
    draws: number,
    win_rate: string,
    created: string,
    updated: string
}
export interface IBasicTeamResult {
    id: number,
    created: string,
    updated: string,
    name: string,
    profiles: string[],
}

export interface ITeamFilters {
    [key: string]: string|number|null|undefined
    offset?: number,
    limit?: number,
    players?: string
    sort?: string
}
export async function fetchTeams(): Promise<ITeamResult[]>
export async function fetchTeams(f: ITeamFilters): Promise<IPagedResult<ITeamResult>>
export async function fetchTeams(f?: ITeamFilters): Promise<ITeamResult[]|IPagedResult<ITeamResult>> {
    const url = filteredEndpoint<ITeamFilters>('/api/teams/', f)
    const result = await axios.get(url)

    return result.data
}

export default fetchTeams