import React from "react";
// @material-ui/core components
import { makeStyles } from "@material-ui/core/styles";


// core components
import GridContainer from "components/Grid/GridContainer.js";
import GridItem from "components/Grid/GridItem.js";
import axios from 'axios'
import Smurfs from 'components/SmurfSummary/SmurfSummary'
import RecentMatches from 'components/MatchSummary/MatchSummary'


import styles from "assets/jss/material-dashboard-pro-react/views/dashboardStyle.js";
import {userInitialState} from '../../variables/general'
import { useStore} from 'react-context-hook'

const useStyles = makeStyles(styles);

async function getSmurfs(user) {
  console.log(` fetching /api/users/${user.user.id}/toons`)
  const response = await axios.get(`/api/users/${user.user.id}/toons`)
  return response.data
}
async function getMatches(filters) {
  const response = await axios.get(`/api/matches/${filters}`)
  return response.data
}

export default function Dashboard() {
  const [user, setUser, deleteUser] = useStore('user', userInitialState)
  const [smurfs, setSmurfs] = React.useState([])
  const [matches, setMatches] = React.useState([])

  React.useEffect(() => {
    getSmurfs(user).then((data) => {
      setSmurfs(data)

      // Get a list of all matches that include the smurfs. Limit it to the last 5
      let filters = '?limit=5&anyplayers='
      for(const profile of data) {
        filters += `${profile.id},`
      }
      getMatches(filters).then(data => {
        setMatches(data)
      })
    })
  }, [])
  return (
    <div>
      
      <GridContainer>
        <GridItem xs={12}>
          
          <Smurfs data={smurfs} />
        </GridItem>
      </GridContainer>
      <GridContainer>
        <GridItem xs={12}>
          
          <RecentMatches data={matches} />
        </GridItem>
      </GridContainer>
    </div>
  );
}
