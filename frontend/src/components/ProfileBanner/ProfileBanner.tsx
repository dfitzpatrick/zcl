import { Avatar, Button, Card, CardActions, CardContent, Chip, createStyles, Grid, ListItem, ListItemAvatar, makeStyles, Theme, Typography } from '@material-ui/core'
import CheckCircleIcon from '@material-ui/icons/CheckCircle'
import HighlightOffIcon from '@material-ui/icons/HighlightOff'
import Skeleton from '@material-ui/lab/Skeleton'
import React from 'react'
import { IProfileResult } from '../../api/profiles'


interface ProfileBannerProps {
  profile: IProfileResult|null
}
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
export default function ProfileBanner<T>(props: ProfileBannerProps) {
  const classes = useStyles()
  const [loading, setLoading] = React.useState(true)
  const profile = props.profile
  const [tabIndex, setTabIndex] = React.useState(0)
  


  if ( profile == null) {
    return <Skeleton height='25vh' />
  } else {
    const verified = (profile.discord_users && profile.discord_users.length > 0)  ?? false
    return (
      <div>
        <Card className={classes.card}>
          <CardContent>
            <Grid container>

              <Grid xs={12}>
                <ListItem>

                  <ListItemAvatar>
                    <Avatar variant="square" className={classes.avatar} src={profile?.avatar_url}>{profile.name}</Avatar>


                  </ListItemAvatar>
                  <Typography variant="h1">{profile?.name}</Typography>

                </ListItem>
              </Grid>

            </Grid>
            <div>
              <Chip
                className={classes.chip}
                color="secondary"
                variant="outlined"
                icon={verified ? <CheckCircleIcon /> : <HighlightOffIcon />}

                label={verified ? "Verified Account" : "Unverified Account"}
              />
             
            </div>


          </CardContent>
          <CardActions>
            <Button variant="outlined" color="secondary" onClick={(e)=>window.location.href=profile.profile_url}>Battle.net Profile</Button>
      
          </CardActions>
        </Card>
        
      </div>
    )
  }

}
