import { Grid, Tab, } from '@material-ui/core'
import TabPanel from '@material-ui/lab/TabPanel'
//import TabPanel from '../../components/TabPanel/TabPanel'
import React from 'react'
import ProfileBanner from '../../components/ProfileBanner/ProfileBanner'
import TeamTable from '../../components/Teams/TeamTable'
import ProfileSummary from './components/ProfileSummary/ProfileSummary'
import MatchTable from '../../components/Matches/MatchTable'
import { useParams } from 'react-router-dom'
import { IProfileResult } from '../../api/teams'
import { fetchProfile, fetchProfileStats, IProfileStats } from '../../api/profiles'
import { Skeleton, TabContext, TabList } from '@material-ui/lab'
import fetchLeaderboards, { ILeaderboardResult } from '../../api/leaderboard'

export default function Profile() {
  const [tabValue, setTabValue] = React.useState("1")
  const [leaderboards, setLeaderboards] = React.useState<ILeaderboardResult[]>([])
  const { profileId } = useParams()
  const [profile, setProfile] = React.useState<IProfileResult | null>(null)
  const [profileStats, setProfileStats] = React.useState<IProfileStats|null>(null)

  React.useEffect(() => {
    fetchProfile(profileId).then(p => {
      console.log(p)
      setProfile(p)
    })
    fetchLeaderboards({profile_id: profileId, offset: 0, limit: 10000}).then(lbs=> {
      setLeaderboards(lbs.results)
    })
    fetchProfileStats(profileId).then(stats=>setProfileStats(stats))
  }, [])
  if (profile == null) {
    return <Skeleton />
  } else {
    return (
      <div>
        <Grid container>
          <Grid item xs={12}>
            <ProfileBanner profile={profile} />
          </Grid>
          <Grid item xs={12}>
            <TabContext value={tabValue}>
              <TabList onChange={(e, v) => setTabValue(v)}>
                <Tab label="Summary" value="1" />
                <Tab label="Matches" value="2" />
                <Tab label="Teams" value="3" />
              </TabList>
        
              <TabPanel value="1">
                <ProfileSummary
                profile={profile}
                leaderboards={leaderboards}
                profileStats={profileStats}
                />
              </TabPanel>

              <TabPanel value="2">
                <MatchTable
                  gridFilterParams={{ xs: 12, md: 4 }}
                  gridItemParams={{ xs: 12, md: 8 }}
                  title={`${profile.name}'s' Matches`}
                  filters={{ players: profile.id }}
                />
              </TabPanel>

              <TabPanel value="3">
                <TeamTable
                  gridFilterParams={{ xs: 12, md: 4 }}
                  gridItemParams={{ xs: 12, md: 8 }}
                  title={`${profile.name}'s' Teams`}
                  filters={{ players: profile.id }}
                />
              </TabPanel>
             
            
            </TabContext>

          </Grid>
        </Grid>
      </div>
    )
  }
}
