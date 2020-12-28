import axios from 'axios'


export interface ICurrentUser {
    avatar: string,
    client_heartbeat: string,
    created: string,
    discriminator: number,
    id: string,
    username: string,
}
export async function fetchCurrentUser(): Promise<ICurrentUser|undefined> {
    const url = '/accounts/me'
    try {
        const result = await axios.get<ICurrentUser>(url, {withCredentials: true})
        return result.data
    } catch (error) {
        return
    }
}
