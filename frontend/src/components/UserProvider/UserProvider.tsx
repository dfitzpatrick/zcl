
import React from 'react'
import { fetchCurrentUser, ICurrentUser } from '../../api/accounts'
import { IProfileResult } from '../../api/teams'
interface IUserProviderProps {

}
export const UserContext = React.createContext<ICurrentUser | undefined>(undefined)

export default function UserProvider(props: React.PropsWithChildren<IUserProviderProps>) {
    const [user, setUser] = React.useState<ICurrentUser | undefined>(undefined)
    React.useEffect(() => {
        fetchCurrentUser().then(u => setUser(u)).catch(reason=>setUser(undefined))
    }, [])
    return (
        <UserContext.Provider value={user}>
            {props.children}
        </UserContext.Provider>
    )
}
