
import { Avatar, Card, createStyles, Divider, Grid, makeStyles, Theme, Typography } from '@material-ui/core'
import React from 'react'
import { ILeaderboardResult } from '../../../api/leaderboard'
import { IMatchRosterResult, IMatchTeamResult } from '../../../api/matches'
import { IProfileResult } from '../../../api/teams'

const useStyles = makeStyles((theme: Theme) => createStyles({
  container: {
    padding: theme.spacing(1),
   
  },
  rosterContainer: {
    margin: theme.spacing(1),
    display: 'flex',
    '& > *': {
      margin: theme.spacing(1),
    },
  },
  card: {
    margin: theme.spacing(2),
    padding: theme.spacing(1),
  },
  colorBlock: {
    padding: '20px',
  }
}))

function getPosition(n: number): string {
  const positions: any = {
    0: "Top Left",
    1: "Top Right",
    2: "Bottom Right",
    3: "Bottom Left",
  }
  return positions[n.toString()]
}
interface IRosterPanelProps {
  rosters: IMatchRosterResult[],
  leaderboards: ILeaderboardResult[],
  profiles: IProfileResult[],
  matchTeams: IMatchTeamResult[],
}

export default function RosterPanel(props: IRosterPanelProps) {
  const classes = useStyles()
  // We map teams in a clockwise fashion. Fix the sort for it to display like
  // we would expect it in a grid
  const sortTeams = [0,1,3,2]
  const matchId = '1550757673' //useParams()
  const [rosters, setRosters] = React.useState<IMatchRosterResult[]>([])
  const [matchTeams, setMatchTeams] = React.useState<IMatchTeamResult[]>([])
  const [profiles, setProfiles] = React.useState<IProfileResult[]>([])
  const [leaderboards, setLeaderboards] = React.useState<ILeaderboardResult[]>([])

  React.useEffect(()=> {
    setRosters(props.rosters)
    setMatchTeams(props.matchTeams)
    setLeaderboards(props.leaderboards)
    setProfiles(props.profiles)
  }, [props.rosters, props.matchTeams, props.leaderboards, props.profiles])

  const getProfileFromRosters = (profileId: string): IProfileResult | undefined => {
    for (const r of rosters) {
      if (r.sc2_profile.id === profileId) {
        return r.sc2_profile
      }
    }
  }
  const getLeaderboard = (profileId: string): ILeaderboardResult | undefined => {

    for (const lb of leaderboards) {
      if (lb.profile.id == profileId) { return lb }
    }
  }

  const ProfileSection = (t: IMatchTeamResult) => {
    const teamRosters = rosters.filter(v => t.team.profiles.includes(v.sc2_profile.id))
    const result = teamRosters.map(r => {
      const lane = () => {
        const p = getProfileFromRosters(r.lane)
        if (p) { return <Typography>(Laning {p.name})</Typography> }
        return ""
      }
      const leaderboard = () => {
        const lb = getLeaderboard(r.sc2_profile.id)
        if (lb) {
          return (
            <Typography>
              #{lb.rank} RANK | {lb.elo} ELO | {lb.wins} WINS | {lb.losses} LOSSES | {lb.win_rate}% WIN RATE
            </Typography>
          )
        } else { return <Typography>NOT CURRENTLY RANKED</Typography> }
      }
      const playerColor = {
        backgroundColor: 'rgba(' + r.color + ')'
    }
      return (
        <>

          <Grid container className={classes.rosterContainer} xs={12}>
            <Grid>
              <Avatar src={r.sc2_profile.avatar_url} alt={r.sc2_profile.name}>{r.sc2_profile.name.charAt(0)}</Avatar>
            </Grid>
            <Grid item className={classes.colorBlock} style={playerColor}>
           
            </Grid>
            <Grid item>
              <div style={{display: 'block'}}>
              <Typography variant="h5">{r.sc2_profile.name}</Typography>
              {lane()}
              </div>
            </Grid>
          </Grid>
          <Grid container>
            <Grid>
              {leaderboard()}
            </Grid>
          </Grid>
          
        </>
      )
    })
    return result

  }


  return (
    <div>
      <Grid container xs={12} className={classes.container}>

        {matchTeams.map(mt => {
          const position = getPosition(mt.position)
          const winnerBadge = mt.outcome === 'win' ? <i className="fas fa-trophy"></i> : ""
          return (
            <Grid item xs={12} sm={6}>
            <Card className={classes.card}>
              <Typography color="secondary" variant="h4">{winnerBadge} {position}</Typography>
              <Divider />
                {ProfileSection(mt)}
              
            </Card>
            </Grid>

          )
        })}

      </Grid>

    </div>
  )
}
