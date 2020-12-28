
import { Card, createStyles, Grid, makeStyles, Theme, Typography } from '@material-ui/core'
import React from 'react'
import { ILeaderboardResult } from '../../../../api/leaderboard'
import { IProfileStats } from '../../../../api/profiles'
import { IProfileResult } from '../../../../api/teams'

const useStyles = makeStyles((theme: Theme) => createStyles({
  leaderboardCard: {
    margin: theme.spacing(2),
    padding: theme.spacing(2),
    minWidth: theme.spacing(30),
  },
  leaderboardCardScoreCard: {
    display: 'flex',
   
  },
  metric: {
    margin: theme.spacing(2)
  }
}))


interface IProfileSummaryProps {
  leaderboards: ILeaderboardResult[],
  profile: IProfileResult|null
  profileStats: IProfileStats|null
}

export default function ProfileSummary(props: IProfileSummaryProps) {
  const classes = useStyles()
  const [leaderboards, setLeaderboards] = React.useState<ILeaderboardResult[]>([])
  const [profile, setProfile] = React.useState<IProfileResult | null>(null)
  const [profileStats, setProfileStats] = React.useState<IProfileStats|null>(null)
  React.useEffect(()=> {
    setLeaderboards(props.leaderboards)
    setProfile(props.profile)
    setProfileStats(props.profileStats)
  }, [props.leaderboards, props.profile, props.profileStats])

  const metricCard = (title: string, metric: string|number, extra?: string) => {
    return (
      <Card className={classes.leaderboardCard}>
      <Typography variant="h4" color="secondary">
        {title.toUpperCase()}
      </Typography>
      <Typography variant="h1">
        {metric}
      </Typography>
      <Typography color="secondary" variant="h5" className={classes.metric}> {extra} </Typography>
    </Card>
    )
  }

const metrics = () => {
  if (profileStats == null) { return "" }
  return (<>
    <Typography variant="h3">Parsed Match Summary</Typography>
    <Grid container>
      <Grid item xs={12} md={6}>
        {metricCard("Total Matches", profileStats.total_matches)}
      </Grid>
      <Grid item xs={12} md={3}>
        {metricCard("Total Wins", profileStats.wins)}
      </Grid>
      <Grid item xs={12} md={3}>
        {metricCard("Total Losses", profileStats.losses)}
      </Grid>
    </Grid>

    <Typography variant="h3">Chat Antics</Typography>
    <Grid container>
      <Grid item xs={12} md={6}>
        {metricCard("Avg All Chats", profileStats.avg_all_chats.toFixed(2))}
      </Grid>
      <Grid item xs={12} md={6}>
        {metricCard("Avg GG Per Match", profileStats.avg_gg_all_chat.toFixed(2), "GOOD GAME!")}
      </Grid>
      </Grid>
    
      <Typography variant="h3">Performance</Typography>
      <Grid container>
      <Grid item xs={12} md={6}>
        {metricCard("Avg Order Killed", profileStats.avg_victim.toFixed(2), "PLAYER TO DIE")}
      </Grid>
      <Grid item xs={12} md={3}>
        {metricCard("Avg First Bunker Cancelled", (profileStats.avg_first_bunker_cancelled*100).toFixed(2), "PERCENT OF GAMES")}
      </Grid>
      <Grid item xs={12} md={3}>
        {metricCard("AVG FIRST TEAM ELIMINATED", (profileStats.avg_first_team_eliminated*100).toFixed(2), "PERCENT OF GAMES")}
      </Grid>
      </Grid>
      <Grid container>
        <Grid item xs={12} md={6}>
          {metricCard("AVG TIMES TO FINAL TWO TEAMS", (profileStats.avg_times_in_final*100).toFixed(2), "PERCENT OF GAMES")}
        </Grid>
        <Grid item xs={12} md={6}>
          {metricCard("WIN RATE AT FINAL MATCH", (profileStats.win_rate_from_final*100).toFixed(2), "PERCENT OF GAMES")}
        </Grid>
      </Grid>
 </> )
}


  const leaderboardCard = (mode: string) => {
    const board = leaderboards.filter((lb)=>lb.mode === mode)[0]
    if (board === undefined) { return "" }
    return (
      <Card className={classes.leaderboardCard}>
        <Typography variant="h4" color="secondary">
          {mode}
        </Typography>
        <Typography variant="h1">
          # {board.rank}
        </Typography>
        <Typography color="secondary" variant="h5" className={classes.metric}> {parseFloat(board.elo).toFixed(0)} ELO </Typography>
        <Grid className={classes.leaderboardCardScoreCard} container>
        <Typography className={classes.metric}> W: {board.wins} </Typography>
        <Typography className={classes.metric}> L: {board.wins} </Typography>
        <Typography className={classes.metric}> WR: {board.win_rate}% </Typography>
        </Grid>
      </Card>
    )
  }
  return (
    <div>
      <Card className={classes.leaderboardCard}>
      <Typography>
        Please note: This is a work in progress. More metrics will be added as they are identified and developed.
        </Typography>
      </Card>
      <Typography variant="h3">Leaderboards</Typography>
      <Grid xs={12} container>
        <Grid item xs={12} md={6} xl={4}>
        {leaderboardCard("2v2v2v2")}
        </Grid>
        <Grid item xs={12} md={6} xl={4}>
        {leaderboardCard("1v1")}
        </Grid>
        <Grid item xs={12} xl={2}>
        {leaderboardCard("3v3v3v3")}
        </Grid>
        <Grid item xs={12} xl={2}>
        {leaderboardCard("1v1v1v1")}
        </Grid>
      </Grid>
      
     {metrics()}



    </div>
  )
}
