import axios from 'axios'
import { IProfileResult } from './teams'

export interface IDiscordUserResult {
    id: string,
    created: string,
    updated: string,
    username: string,
    discriminator: number,
    avatar: string,
    client_heartbeat: string|null
}
export interface IAccountConnectionResult {
    id: number,
    created: string,
    updated: string,
    provider: string,
    username: string,
    extra_data: {},
    user: string

}
export async function fetchUserProfiles(userId: string): Promise<IProfileResult[]|undefined> {
    const url = `/api/users/${userId}/profiles`
    try {
        const result = await axios.get<IProfileResult[]>(url, {withCredentials: true})
        return result.data
    } catch (error) {
        return
    }
}
export async function fetchUserConnections(userId: string): Promise<IAccountConnectionResult[]> {
    const url = `/api/users/${userId}/connections`
    const result = await axios.get(url, {withCredentials: true})
    return result.data
}
export async function removeUserConnection(connectionId: number) {
    axios.defaults.xsrfCookieName = 'csrftoken'
    axios.defaults.xsrfHeaderName = 'X-CSRFToken'
    const url = `/api/connections/${connectionId}/`
    const result = await axios.delete(url, {    
        withCredentials: true
        }    
    )
    return result.status
}