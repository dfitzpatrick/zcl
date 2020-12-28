
import axios from 'axios'
import {filteredEndpoint, IPagingFilters, IPagedResult } from './apiCommon'

export interface IProfileResult {
    id: string,
    created: string,
    name: string,
    profile_url: string,
    avatar_url: string
    discord_users?: string[]
  }

export interface IProfileStats {
  total_matches: number,
  wins: number,
  losses: number,
  avg_gg_all_chat: number,
  avg_victim: number,
  avg_all_chats: number,
  avg_first_bunker_cancelled: number,
  avg_first_team_eliminated: number,
  avg_times_in_final: number,
  win_rate_from_final: number
}
  export interface IProfileFilters extends IPagingFilters {
    [key: string]: string | number | null | undefined
    name?: string,
    sort?: string
  }

  export default async function fetchProfiles(filters?: IProfileFilters): Promise<IProfileResult[]|IPagedResult<IProfileResult>> {
    const url = filteredEndpoint<IProfileFilters>('/api/profiles', filters)
    const result = await axios.get(url)
    return result.data
  }


export  async function fetchProfile(id: string): Promise<IProfileResult> {
    const url = `/api/profiles/${id}`
    const result = await axios.get(url)
    return result.data
  }

  // TODO: Do something that resembles a better practice
  export async function fetchProfileStats(id: string): Promise<IProfileStats|null> {
    const url = `/api/playerstats/${id}`
    const result = await axios.get(url)
      return (result.status === 200) ? result.data : null
  }