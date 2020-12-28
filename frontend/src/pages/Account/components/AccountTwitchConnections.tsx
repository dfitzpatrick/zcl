
import { Button, Card, IconButton, ListItem, ListItemAvatar, ListItemSecondaryAction, ListItemText, makeStyles, createStyles, Theme } from '@material-ui/core'
import React from 'react'
import { IAccountConnectionResult, fetchUserConnections, removeUserConnection } from '../../../api/users'
import { UserContext } from '../../../components/UserProvider/UserProvider'
import DeleteIcon from '@material-ui/icons/Delete';
const useStyles = makeStyles((theme: Theme) => createStyles({
  cardContainer: {
    marginTop: theme.spacing(2)
  },
  card: {
    maxWidth: '300px',
    margin: theme.spacing(1)
  },
  listItem: {
    listStyleType: 'none !important'
  }

}))

export default function AccountTwitchConnections() {
  const classes = useStyles()
  const user = React.useContext(UserContext)
  const [twitchConnections, setTwitchConnections] = React.useState<IAccountConnectionResult[]>([])
  React.useEffect(() => {
    if (user) {
      fetchUserConnections(user.id)
        .then(connections => setTwitchConnections(connections.filter((c) => c.provider === 'twitch')))
    }
  }, [user])
  const deleteButtonHandler = (connectionId: number) => {
    removeUserConnection(connectionId).then(() => {
      setTwitchConnections(twitchConnections.filter(item => item.id !== connectionId))
    })
  }
  return (<>
    <div>
      <Button variant="contained"
        onClick={() => window.location.href = '/accounts/twitch/connect'}>Add New Twitch Connection</Button>
    </div>
    <div className={classes.cardContainer}> 
      {twitchConnections.map(item => (
        <Card className={classes.card}>
            <ListItem className={classes.listItem}>
          <ListItemAvatar>
            <i className="fab fa-twitch" style={{ fontSize: '2em' }} aria-hidden="true"></i>
          </ListItemAvatar>
          <ListItemText primary={item.username} secondary={item.provider} />
          <ListItemSecondaryAction>
            <IconButton key={item.id} edge="end" aria-label="delete" onClick={(e) => deleteButtonHandler(item.id)}>
              <DeleteIcon />
            </IconButton>
          </ListItemSecondaryAction>
        </ListItem>
        </Card>
        
      ))}
    </div>
  </>
  )
}
