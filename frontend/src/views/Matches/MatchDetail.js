import React from 'react'
import { useParams } from 'react-router-dom'
import GridContainer from "components/Grid/GridContainer.js";
import GridItem from "components/Grid/GridItem.js";
import Card from "components/Card/Card.js";
import CardBody from "components/Card/CardBody.js";
import CardIcon from "components/Card/CardIcon.js";
import Button from "components/CustomButtons/Button.js";
import CardHeader from "components/Card/CardHeader.js";
import { cardTitle } from "assets/jss/material-dashboard-pro-react.js";
import { makeStyles } from "@material-ui/core/styles";
import axios from "axios";
import moment from 'moment';

import Heading from "components/Heading/Heading.js";
// @material-ui/icons
import CloudDownloadIcon from '@material-ui/icons/CloudDownload';
import Container from '@material-ui/core/Container';
import StatsTrend from "components/StatsTrend/StatsTrend.js"
// core components
import UpgradeViewer from "components/UpgradeViewer/UpgradeViewer.js"
import FeedChart from "components/FeedChart/FeedChart.js"
import RosterBadge from "components/RosterBadge/RosterBadge.js"
import UnitStatistics from "components/UnitStatistics/UnitStatistics.js"
import tankIcon from "assets/img/unitIcons/tank.png"
import bunkerIcon from "assets/img/unitIcons/bunker.png"
import Timeline from "components/Timeline/Timeline.js";
import NavPills from "components/NavPills/NavPills.js";
import { dataTable } from 'variables/general';

const styles = {
    cardIconTitle: {
        ...cardTitle,
        marginTop: "15px",
        marginBottom: "0px"
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
    }
};

const useStyles = makeStyles(styles);

async function getMatch(id) {
    const response = await axios.get(`/api/matches/${id}`)
    return response.data

}
async function getMatchEvents(id) {
    const response = await axios.get(`/api/matches/${id}/events`)
    return response.data
}
async function getLeaderboards(teams) {
    const boardIds = []
    for (const team of teams) {
        for (const r of team.rosters) {
            const lb = r.sc2_profile.leaderboard
            if (lb != null) {
                boardIds.push(lb)
            }
        }

    }

    const filter = boardIds.join()
    const response = await axios.get(`/api/leaderboards/?id=${filter}`)
    return response.data
}

async function getChartData(id) {
    const filter = '?charts=feed,time_series,unit_stats,upgrades'
    const target = `/api/charts/${id}/${filter}`
    const response = await axios.get(target)
    return response.data
}



const initialState = {
    loading: true,
    data: {},
    events: []
}
const initialChartState = {
    time_series: [],
    feed: [],
    upgrades: [],
    unit_stats: [],
}
function compare(a, b) {
    let at = parseFloat(a.game_time)
    let bt = parseFloat(b.game_time)
    if (at > bt) return 1
    if (bt > at) return -1
    return 0
}
function formatLineData(data, propertyName) {
    var players = {}
    var result = []
    //Use profile as a  key in case there are duplicate player names. 
    for (const p of data) {
        let game_time = moment.utc(p.game_time * 1000).format('HH:mm:ss');
        //let game_time = p.game_time
        if (!players.hasOwnProperty(p.profile)) {
            // No name yet. Add data column
            players[p.profile] = { name: p.name, data: [] }
        }
        players[p.profile].data.push({
            x: p.game_time,
            y: p[propertyName]
        })
    }
    for (const p in players) {
        result.push({ id: players[p].name, data: players[p].data.sort(compare) })
    }
    return result
}
function teamSort(a, b) {
    const at = a.position
    const bt = b.position
    if (at > bt) return 1
    if (at < bt) return -1
    return 0
}
const story2 = [{
    // First story
    inverted: true,
    badgeColor: "danger",
    badgeIcon: tankIcon,
    title: "Some Title",
    titleColor: "danger",
    body: (
      <p>
        Wifey made the best Father{"'"}s Day meal ever. So thankful so happy so
        blessed. Thank you for making my family We just had fun with the
        “future” theme !!! It was a fun night all together ... The always rude
        Kanye Show at 2am Sold Out Famous viewing @ Figueroa and 12th in
        downtown.
      </p>
    ),
    footerTitle: "11 hours ago via Twitter"
  },]



export default function MatchDetail(props) {

    const [data, setData] = React.useState(initialChartState)
    const [match, setMatch] = React.useState(initialState)
    const [leaderboardData, setLeaderboardData] = React.useState([])

    const classes = useStyles()
    const id = useParams()

    React.useEffect(() => {
        const { id } = props.match.params
        getMatch(id).then(m => {
            getChartData(id).then(chart => {
                setData(chart)
            })
            getMatchEvents(id).then(me => {
                //setData(allData)
                setMatch({ loading: false, data: m, events: me })
            })
            getLeaderboards(m.teams).then(lb => {
                setLeaderboardData(lb)
            })
        })

    }, [])
    if (match.loading) {
        return (
            <GridContainer>
                <GridItem xs={12}>
                    <Card>
                        <CardHeader color="primary" icon>
                            <CardIcon color="danger">
                                LB
            </CardIcon>
                            <h4 className={classes.cardIconTitle}>Matches</h4>
                        </CardHeader>
                        <CardBody>
                            Loading Data
        </CardBody>
                    </Card>
                </GridItem>
            </GridContainer>
        )
    } else {
        const m = match.data

        const upgrades = () => {
            return (<div>
                <Heading title="Upgrades" />
                <UpgradeViewer data={data.upgrades} />
            </div>)
        }
        const stories = match.events.map((me, index) => {
            const defaults = {
                title: "Game Event",
                color: "success",
                icon: tankIcon,

            }
            const key_names = {
                player_nuked: {
                    title: "Nukes",
                    color: "success",
                    icon: tankIcon,
                },
                bunker_started: 
                {
                    title: "Builds a Bunker",
                    color: "success",
                    icon: bunkerIcon,
                },
                bunker_killed: {
                    title: "Destroys a Bunker",
                    color: "danger",
                    icon: bunkerIcon,
                },
                player_leave: {
                    title: "Rages Out of the Game",
                    color: "danger",
                    icon: tankIcon,
                },
                player_died: {
                    title: "Eliminates a Player",
                    color: "danger",
                    icon: tankIcon,
                },
            }
            
            const obj = key_names.hasOwnProperty(me.key) ? key_names[me.key] : defaults
          return ({
              inverted: obj.color == 'danger',
              badgeColor: obj.color,
              badgeIcon: obj.icon,
              title: me.profile.name + " " + obj.title,
              titleColor: obj.color,
              body: me.description,
              footerTitle: moment.utc(me.game_time*1000).format("H:mm:ss")
          })
        })
        return (
            <div>
                

                <GridContainer>
                    <GridItem xs={12}>
                        <Card>
                            <CardHeader color="primary" icon>
                                <CardIcon color="danger">
                                    DETAILS
                                </CardIcon>
                                <h4 className={classes.cardIconTitle}>Game Details</h4>
                            </CardHeader>
                            <CardBody>
                                <GridContainer>
                                    <GridItem xs={12} sm={6} md={6}>

                                    
                                    <GridContainer>
                                        <GridItem className={classes.detailsHeader} >
                                            Match Date:
                                        </GridItem>
                                        <GridItem className={classes.detailsValue}>
                                           {moment(match.data.match_date).format("dddd, MMMM Do YYYY, h:mm:ss a")}
                                        </GridItem>
                                    </GridContainer>

                                    <GridContainer>
                                        <GridItem className={classes.detailsHeader}>Players:</GridItem>
                                        <GridItem className={classes.detailsValue}>{match.data.players}</GridItem>

                                    </GridContainer>

                                    <GridContainer>
                                        <GridItem className={classes.detailsHeader}>Game Length:</GridItem>
                                        <GridItem className={classes.detailsValue}>{moment.utc(match.data.game_length * 1000).format('HH:mm:ss')}</GridItem>
                                    </GridContainer>
                               
                                </GridItem>
                                <GridItem xs={12} sm={6} md={6}>

                                    <GridContainer>
                                        <GridItem className={classes.detailsHeader}>Winners</GridItem>
                                        <GridItem className={classes.detailsValue}>{match.data.winners}</GridItem>
                                    </GridContainer>
                                    <GridContainer>
                                        <GridItem className={classes.detailsHeader}>League</GridItem>
                                        <GridItem className={classes.detailsValue}>{match.data.league || "Public Game"}</GridItem>

                                    </GridContainer>
                                    <GridContainer>
                                        <GridItem className={classes.detailsHeader}>Season</GridItem>
                                        <GridItem className={classes.detailsValue}>{match.data.season || "No Season"}</GridItem>
                                    </GridContainer>
                                </GridItem>
                                </GridContainer>
                                <Button color="info" round href={`https://zcleagues.s3-us-west-1.amazonaws.com/replays/${match.data.id}.SC2Replay`}><CloudDownloadIcon /> Download Replay</Button>
                            </CardBody>
                        </Card>
                    </GridItem>
                </GridContainer>
                <hr />
                <NavPills
                color="warning"
                tabs={[

                {
                    tabButton: "Roster",
                    tabContent: (
                        <GridContainer>
                            <GridItem xs={12} sm={7} md={7}>
                                <Heading title="Roster" />
                                <GridContainer>
                                    {match.data.teams.sort(teamSort).map(t => {
                                        return (<>
                                            <GridItem xs={12} sm={6} md={6}>
                                                <RosterBadge team={t} leaderboardData={leaderboardData} />
                                            </GridItem>
                                        </>)
                                    })}



                                </GridContainer>
                            </GridItem>
                            
                        </GridContainer>
                    )
                },
                {
                    tabButton: "Feed Bar",
                    tabContent: (
                        <GridContainer xs={12} sm={12} md={12}>
                            <GridItem xs={12} sm={3} md={5}>
                                <Heading title="Feed Summary" />
                                    <FeedChart data={dataTable.feed} />
                            </GridItem>
                        </GridContainer>

                    )
                },
                {
                    tabButton: "Charts",
                    tabContent: <StatsTrend data={data.time_series} />,
                  },
                  {
                      tabButton: "Upgrades",
                      tabContent:  <UpgradeViewer data={data.upgrades} />
                  },
                  {
                      tabButton: "Unit Statistics",
                      tabContent: <UnitStatistics data={data.unit_stats} />  
                  },
                  {
                    tabButton: "Events",
                    tabContent: <Timeline stories={stories} />,
                  },
                  
                 
                ]}
                />
                
                
         

                

              
         
                
     

            </div>

        )


    }
}
