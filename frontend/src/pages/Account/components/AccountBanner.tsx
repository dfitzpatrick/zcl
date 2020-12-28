import { Avatar, Card, CardActions, CardContent, Chip, createStyles, Grid, ListItem, ListItemAvatar, makeStyles, Theme, Typography } from '@material-ui/core'
import CheckCircleIcon from '@material-ui/icons/CheckCircle'
import HighlightOffIcon from '@material-ui/icons/HighlightOff'
import Skeleton from '@material-ui/lab/Skeleton'
import React from 'react'
import { ICurrentUser } from '../../../api/accounts'
import { UserContext } from '../../../components/UserProvider/UserProvider'


const useStyles = makeStyles((theme: Theme) => createStyles({
  avatar: {
    width: theme.spacing(12),
    height: theme.spacing(12)
  },
  chip: {
    margin: '0.5vh'
  },
  card: {
    margin: '1em'
  }

}))
export default function AccountBanner<T>() {
  const user: ICurrentUser|undefined = React.useContext(UserContext)
  const classes = useStyles()




  if (user == undefined) {
    return <Skeleton height='25vh' />
  } else {
    const clientInstalled = user.client_heartbeat == null
    const avatar = `https://cdn.discordapp.com/avatars/${user.id}/${user.avatar}.png`
    return (
      <div>
        <Card className={classes.card}>
          <CardContent>
            <Grid container>

              <Grid xs={12}>
                <ListItem>

                  <ListItemAvatar>
                    <Avatar variant="square" className={classes.avatar} src={avatar}></Avatar>


                  </ListItemAvatar>
                  <Typography variant="h1">{user.username}</Typography>

                </ListItem>
              </Grid>

            </Grid>
            <div>
              <Chip
                className={classes.chip}
                color="secondary"
                variant="outlined"
                icon={clientInstalled ? <CheckCircleIcon /> : <HighlightOffIcon />}

                label={clientInstalled ? "Client Installed" : "Client NOT Installed"}
              />

            </div>


          </CardContent>
          <CardActions>

          </CardActions>
        </Card>

      </div>
    )
  }

}
