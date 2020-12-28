import { Tab } from '@material-ui/core'
import { TabContext, TabList } from '@material-ui/lab'
import TabPanel from '@material-ui/lab/TabPanel'
import _ from 'lodash'
import React from 'react'
import { useParams } from 'react-router-dom'
import fetchLeaderboards, { ILeaderboardResult } from '../../api/leaderboard'
import { fetchMatch, fetchMatchRosters, fetchMatchTeams, IMatchResult, IMatchRosterResult, IMatchTeamResult } from '../../api/matches'
import { IProfileResult } from '../../api/teams'
import MarginContainer from '../../components/MarginContainer/MarginContainer'
import RosterPanel from './components/RosterPanel'
import FeedChart from './components/FeedChart'
import MatchBanner from './components/MatchBanner'
import TimeCharts from './components/TimeCharts'
import { IChartResponse, fetchCharts } from '../../api/charts'
interface IMatchDetailProps {

}

export default function MatchDetail(props: IMatchDetailProps) {
  const [match, setMatch] = React.useState<IMatchResult | null>(null)
  const { matchId } = useParams()
  const [tabIndex, setTabIndex] = React.useState(0)
  const [tabValue, setTabValue] = React.useState("rosters")
  const [rosters, setRosters] = React.useState<IMatchRosterResult[]>([])
  const [matchTeams, setMatchTeams] = React.useState<IMatchTeamResult[]>([])
  const [profiles, setProfiles] = React.useState<IProfileResult[]>([])
  const [leaderboards, setLeaderboards] = React.useState<ILeaderboardResult[]>([])
  const [chartData, setChartData] = React.useState<IChartResponse>({})
   // We map teams in a clockwise fashion. Fix the sort for it to display like
  // we would expect it in a grid
  const sortTeams = [0,1,3,2]

  React.useEffect(() => {
    fetchMatch(matchId).then(m => {
      setMatch(m)
    })
    fetchMatchTeams(matchId).then(ts => {
      const profileIdss = ts.map(o=>o.team.profiles).join(',')
      setMatchTeams(_.sortBy(ts, (o) => { return _.indexOf(sortTeams, o.position)}))
      

    })
    fetchMatchRosters(matchId).then(rs => {
      const profiles = rs.map(v => v.sc2_profile)
      const profileIds = profiles.map(p=> p.id)
      setRosters(rs)
      setProfiles(profiles)
      fetchLeaderboards({
        mode: '2v2v2v2',
        profile_id: profileIds.join(','),
        limit: 10000,
        offset: 0,
      }).then(lbs=> {
        setLeaderboards(lbs.results)
    })
    })
    fetchCharts(matchId).then(charts=>setChartData(charts))
    
  }, [])
  return (
    <MarginContainer>
      <MatchBanner
        match={match}
      />
      <TabContext value={tabValue}>
        <TabList onChange={(e,v)=>setTabValue(v)}>
        <Tab label="Roster" value="rosters" />
        <Tab label="Feed Chart" value="feed" />
        <Tab label="Time Charts" value="charts" />
        </TabList>

        <TabPanel value="rosters">
        <RosterPanel
        rosters={rosters}
        matchTeams={matchTeams}
        profiles={profiles}
        leaderboards={leaderboards}
        />
      </TabPanel>
      <TabPanel value="feed">
        <FeedChart data={chartData.feed ?? []}/>
      </TabPanel>
      <TabPanel value="charts">
        <TimeCharts data={chartData.time_series ?? []} />
      </TabPanel>
      </TabContext>


      
      </MarginContainer>
  )
}
