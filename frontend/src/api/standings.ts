import axios from 'axios'
import { filteredEndpoint } from "./apiCommon"

export interface IStandingFilters {
    [key: string]: string|number|null|undefined
    offset?: number,
    limit?: number,
    league?: string,
    season?: string,

}
export interface IStandingResult {
    id: string,
    name: string,
    total_matches: number,
    total_wins: number,
    total_losses: number,
    total_draws: number,
    rate: number,
    win_rate: number,
    adjusted_win_rate: number,
    rank: number,
    avatar_url: string
}

export default async function fetchStandings(f: IStandingFilters) {
    const url = filteredEndpoint<IStandingFilters>('/api/standings/', f)
    const result = await axios.get(url)
    return result.data
    
}