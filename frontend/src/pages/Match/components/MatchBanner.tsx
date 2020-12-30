import { Button, Card, CardContent, createStyles, Grid, makeStyles, Theme, Typography } from '@material-ui/core'
import CloudDownloadIcon from '@material-ui/icons/CloudDownload'
import moment from 'moment'
import React from 'react'
import { IMatchResult } from '../../../api/matches'


interface IMatchBannerProps {
  match: IMatchResult | null
}
const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    fontSize: '1.5em',
    padding: '10px'
  },
  detailsHeader: {
    backgroundColor: 'whitesmoke',
    margin: '5px',
    fontSize: '1.5em',
    fontWeight: 'bold',
  },
  detailsValue: {
    margin: '5px',
    fontSize: '1.5em',
  },
  cardContent: {
    margin: '1em'
  }

}))

export default function MatchBanner(props: IMatchBannerProps) {
  const classes = useStyles()
  const match = props.match
  if (match == null) { return <div>Loading</div> }
  return (
    <div>
      <Grid>
        <Grid item xs={12}>
          <Card>
            <CardContent className={classes.cardContent}>
            <Typography variant="h4">Game Details</Typography>
            <Grid container className={classes.root}>
              <Grid item xs={12} sm={6} md={6}>
                <Grid container>
                  <Grid item >
                    <Typography color="secondary">Match Date:</Typography>
                  </Grid>
                  <Grid item>
                    <Typography>
                      {moment(match.match_date).format("dddd, MMMM Do YYYY, h:mm:ss a")}
                    </Typography>

                  </Grid>
                </Grid>

                <Grid container>
                  <Grid item>
                    <Typography color="secondary">Players:</Typography>
                  </Grid>
                  <Grid item><Typography>{match.names}</Typography></Grid>

                </Grid>

                <Grid container>
                  <Grid item>
                  <Typography color="secondary">Game Length:</Typography>
                  </Grid>
                  <Grid item><Typography>{moment.utc(match.game_length * 1000).format('HH:mm:ss')}</Typography></Grid>
                </Grid>

              </Grid>
              <Grid item xs={12} sm={6} md={6}>

                <Grid container>
                  <Grid item>
                  <Typography color="secondary">
                    Winners: 
                    </Typography></Grid>
                  <Grid item><Typography>{match.alt_winners}</Typography></Grid>
                </Grid>
                <Grid container>
                  <Grid item>
                  <Typography color="secondary">League</Typography></Grid>
                  <Grid item>
                 <Typography>{match.league || "Public Game"}</Typography></Grid>

                </Grid>
                <Grid container>
                  <Grid item>
                  <Typography color="secondary">
                    Season</Typography></Grid>
                  <Grid item><Typography>{match.season || "No Season"}</Typography></Grid>
                </Grid>
              </Grid>
            </Grid>
            <Button variant="contained" color="secondary" href={`https://zcleagues.s3-us-west-1.amazonaws.com/replays/${match.id}.SC2Replay`}><CloudDownloadIcon /> Download Replay</Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </div>
  )
}
