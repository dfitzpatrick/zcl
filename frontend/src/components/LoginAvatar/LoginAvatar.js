import React from 'react'
import { useStore } from 'react-context-hook'
import {userInitialState} from '../../variables/general'
import Avatar from '@material-ui/core/Avatar';
export default function LoginAvatar() {
    const [user, setUser, deleteUser] = useStore('user', userInitialState)
    const details = user.user
    const avatar = () => {
        if (details) {
            return (
            <Avatar alt={details.username} src={details.avatar_url}></Avatar>
            )
        }
        return <Avatar />
    }
    return (
        <>
        {avatar()}
        </>
    )
}
