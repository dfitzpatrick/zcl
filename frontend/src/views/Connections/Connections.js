import React from 'react'
import { useStore } from 'react-context-hook'
import { makeStyles } from '@material-ui/core/styles';
import {userInitialState} from "variables/general.js"
import axios from 'axios'
import Heading from "components/Heading/Heading.js"
import Button from "components/CustomButtons/Button.js"
import List from '@material-ui/core/List';
import ListItem from '@material-ui/core/ListItem';
import ListItemText from '@material-ui/core/ListItemText';
import ListItemAvatar from '@material-ui/core/ListItemAvatar';
import Avatar from '@material-ui/core/Avatar'
import ListItemSecondaryAction from '@material-ui/core/ListItemSecondaryAction';
import IconButton from '@material-ui/core/IconButton';
import DeleteIcon from '@material-ui/icons/Delete';

const useStyles = makeStyles((theme) => ({
    root: {
      width: '100%',
      maxWidth: 360,
      backgroundColor: theme.palette.background.paper,
    },
    largeIcon: {
        fontSize: '2em',
    }
  }));


async function getConnections(user) {
    
    const response = await axios.get(`/api/users/${user.user.id}/connections`, {
        headers: {
            'Authorization': `Token ${user.token}`
        }
    })
    return response.data
}
async function deleteConnection(user, id) {
    const response = await axios.delete(`/api/connections/${id}/`, {
        headers: {
            'Authorization': `Token ${user.token}`
        }
    })
    console.log('response')
    console.log(response)
    return response.data
}

export default function Connections() {
    const classes = useStyles();
    const [user] = useStore('user', userInitialState)
    const [connections, setConnections] = React.useState([])

    const deleteButtonHandler = (id) => {
        deleteConnection(user, id).then(() => {
            setConnections(connections.filter(item => item.id !== id))
        })
    }
    const newTwitchHandler = () => {
        window.location.href = '/accounts/twitch/connect'
    }
    React.useEffect(() => {
        getConnections(user).then(conns => {
            setConnections(conns)
        })
    }, [])
    
    return (
        <div>
            <Heading
                textAlign="left"
                title="Connections"
            />
            <Button color="primary" round onClick={newTwitchHandler}>
                <i class="fab fa-twitch" aria-hidden="true"></i>
                 New Twitch Connection
            </Button>
            <hr />
            <List className={classes.root}>
            {connections.map(item => {
                return (
                <ListItem key={item.id}>
                <ListItemAvatar>
                <i class="fab fa-twitch" style={{fontSize: '2em'}}  aria-hidden="true"></i>
                </ListItemAvatar>
                <ListItemText primary={item.username} secondary={item.provider} />
                <ListItemSecondaryAction>
                    <IconButton key={item.id} edge="end" aria-label="delete" onClick={(e) => deleteButtonHandler(item.id)}>
                      <DeleteIcon />
                    </IconButton>
                  </ListItemSecondaryAction>
            </ListItem>
                )
     
            })}
                 </List> 
            
        </div>
    )
}
