import axios from 'axios'
import { filteredEndpoint, IPagedResult } from './apiCommon'
import { IBasicTeamResult, IProfileResult } from './teams'

export async function fetchMatches(): Promise<IMatchResult[]>

export async function fetchMatches(f: IMatchFilters): Promise<IPagedResult<IMatchResult>>
export async function fetchMatches(f?: IMatchFilters): Promise<IMatchResult[]|IPagedResult<IMatchResult>> {
    const url = filteredEndpoint<IMatchFilters>('/api/matches/', f)
    const result = await axios.get(url)
    return result.data
    
}
export async function fetchMatch(id: string): Promise<IMatchResult> {
    const url = `/api/matches/${id}`

    const result = await axios.get(url)
    return result.data
}

export async function fetchMatchTeams(id: string): Promise<IMatchTeamResult[]> {
    const url = `/api/matches/${id}/teams`
    const result = await axios.get(url)
    return result.data
}
export async function fetchMatchRosters(id: string): Promise<IMatchRosterResult[]> {
    const url = `/api/matches/${id}/rosters`
    const result = await axios.get(url)
    return result.data
}
export interface IMatchFilters {
    [key: string]: string|number|null|undefined
    offset?: number,
    limit?: number,
    players?: string,
    sort?: string,
    ranked?: string,
    before_date?: string,
    after_date?: string,
    league?: string,
    season?: string
}
export interface IMatchQuery {
    count: number,
    next: string,
    previous: string,
    results: IMatchResult[]
}

export interface IMatchResult {
    id: string,
    created: string,
    updated: string,
    match_date: string,
    players: string,
    profile_ids: string,
    winner_ids: string,
    winners: string,
    game_length: number,
    league: number,
    season: number,
    tanks: number|null,
    turrets: number|null,
    nukes: number|null,
    elo_average: number

}
export interface IMatchTeamResult {
    id: number,
    created: string,
    updated: string,
    position: number,
    elo_average: number,
    outcome: string,
    victim_number: number,
    match: string,
    team: IBasicTeamResult
}

export interface IMatchRosterResult {
    id: number,
    sc2_profile: IProfileResult
    created: string,
    updated: string,
    team_number: number,
    position_number: number,
    color: string,
    elo: number,
    leaderboard_ranking: number,
    match: string,
    lane: string,
    team: number
}
export default fetchMatches