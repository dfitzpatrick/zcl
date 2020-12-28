import React from 'react'
import {
  BrowserRouter as Router,

  Route, Switch
} from "react-router-dom"
import { ICurrentUser } from "./api/accounts"
import './App.css'
import Leaderboard from "./components/Leaderboard/Leaderboard"
import LeagueTable from "./components/Leagues/LeagueTable"
import MatchTable from "./components/Matches/MatchTable"
import MenuAppBar from "./components/MenuAppBar"
import UserProvider from "./components/UserProvider/UserProvider"
import Account from "./pages/Account/Account"
import Error from "./pages/Error/Error"
import Home from "./pages/Home/Home"
import MatchDetail from "./pages/Match/MatchDetail"
import Profile from "./pages/Profile/Profile"
import PrivateRoute from './components/PrivateRoute/PrivateRoute'

function App() {



  return (
    <>
      <UserProvider>
        <Router>
          <MenuAppBar />

          <Switch>
            <Route exact path='/'>
              <Home />
            </Route>
            <Route path='/leaderboard'>
              <Leaderboard
                gridItemParams={{ xs: 12, md: 9 }}
                gridFilterParams={{ xs: 12, md: 3 }}
                title="Public Leaderboard"
              />
            </Route>
            <Route exact path='/matches'>
              <MatchTable
                gridItemParams={{ xs: 12, md: 9 }}
                gridFilterParams={{ xs: 12, md: 3 }}
                title="Completed Matches"
              />
            </Route>
            <Route path='/account'>
              <Account />
            </Route>
            <Route path='/matches/:matchId'>
              <MatchDetail />
            </Route>
            <Route path='/profiles/:profileId'>
              <Profile />
            </Route>
            <Route path='/error'>
              <Error />
            </Route>

            <Route path='/leagues'>
              <LeagueTable
                gridItemParams={{ xs: 12, md: 9 }}
                gridFilterParams={{ xs: 12, md: 3 }}
                title="League Standings"
              />
            </Route>

          </Switch>


        </Router>
      </UserProvider>
    </>

  )
}

export default App;
