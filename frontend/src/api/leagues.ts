import axios from 'axios'
import { filteredEndpoint, IPagedResult } from './apiCommon'


export  async function fetchLeagues(): Promise<ILeagueResult[]>
export async function fetchLeagues(f: ILeagueFilters): Promise<IPagedResult<ILeagueResult>>
export async function fetchLeagues(f?: ILeagueFilters): Promise<ILeagueResult[]|IPagedResult<ILeagueResult>> {
    const url = filteredEndpoint<ILeagueFilters>('/api/leagues/', f)
    const result = await axios.get(url)
    return result.data
}
export interface ILeagueFilters {
    [key: string]: string|number|null|undefined
    offset?: number,
    limit?: number,
    league?: string,
    season: string,
}
export interface ISeasonResult {
    id: number,
    name: string,
    description: string
}
export interface ILeagueResult {
    id: number,
    name: string,
    guild: number,
    description: string
    seasons: ISeasonResult[]
}
export default fetchLeagues