

import { Card, CardActionArea, CardContent, CardMedia, createStyles, Grid, makeStyles, Theme, Typography } from '@material-ui/core'
import moment from 'moment'
import React from 'react'
import { IProfileResult } from '../../../api/teams'
import { fetchUserProfiles } from '../../../api/users'
import { UserContext } from '../../../components/UserProvider/UserProvider'
const useStyles = makeStyles((theme: Theme) => createStyles({
    root: {
      '& > *': {
        margin: theme.spacing(2),
      },
      '& last-child': {
        marginBottom: 0,
        backgroundColor: 'red',
      }
    }
  }))

export default function AccountProfiles() {
    const classes = useStyles()
    const [userProfiles, setUserProfiles] = React.useState<IProfileResult[]>([])
    const user = React.useContext(UserContext)
    React.useEffect(()=> {
        user && fetchUserProfiles(user.id).then(ps=> {
            ps && setUserProfiles(ps)
        })
    },[user])
    return (
        <div>
            <Grid container className={classes.root}>
            {userProfiles.map(p=> {
                return (
                        <Card style={{minWidth: '200px', maxWidth: '200px'}}>
                            <CardActionArea
                            onClick={(e)=>window.location.href=`/profiles/${p.id}`}
                            >
                            <CardMedia
                            image={p.avatar_url}
                            component="img"
                            style={{height: '190px'}}
                            title={p.name}
                            />
                            <CardContent>
                                <Typography variant="h5" component="h2">{p.name}</Typography>
                              
                                <Typography>Created: {moment(p.created).format("YYYY/MM/DD")}</Typography>
                         
                            </CardContent>
                            </CardActionArea>
                        </Card>
             
                )
            })|| <Typography variant="h2">No Rosters to display</Typography>}
      </Grid>
        </div>
    )
}
