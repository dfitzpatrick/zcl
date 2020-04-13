
import Dashboard from "views/Dashboard/Dashboard.js";
import HomePage from "views/Pages/HomePage.js";
import Leaderboard from "views/Leaderboard/Leaderboard.js"
import TeamLeaderboard from "views/Leaderboard/TeamLeaderboard.js"
import DashboardIcon from "@material-ui/icons/Dashboard";
import MatchView from "views/Matches/Matches.js";
import Connections from "views/Connections/Connections.js"

var dashRoutes = [
  {
    path: "/dashboard",
    name: "Dashboard",
    rtlName: "لوحة القيادة",
    icon: DashboardIcon,
    component: Dashboard,
    layout: "/portal"
  },
  {
    path: "/leaderboard",
    name: "Public Leaderboard",
    rtlName: "لوحة القيادة",
    icon: DashboardIcon,
    component: Leaderboard,
    layout: "/portal"
  },
  {
    path: "/teams",
    name: "Team Leaderboard",
    rtlName: "لوحة القيادة",
    icon: DashboardIcon,
    component: TeamLeaderboard,
    layout: "/portal"
  },
  {
    path: "/matches",
    name: "View Matches",
    rtlName: "لوحة القيادة",
    icon: DashboardIcon,
    component: MatchView,
    layout: "/portal"
  },
  {
    path: "/connections",
    name: "Connections",
    rtlName: "لوحة القيادة",
    icon: DashboardIcon,
    component: Connections,
    layout: "/portal"
  },

];
export default dashRoutes;
