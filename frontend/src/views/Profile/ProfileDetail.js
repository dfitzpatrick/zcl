import React from 'react'
import axios from 'axios'
import { useParams } from 'react-router-dom'

import GridContainer from "components/Grid/GridContainer.js";
import GridItem from "components/Grid/GridItem.js";
import Card from "components/Card/Card.js";
import CardBody from "components/Card/CardBody.js";
import CardIcon from "components/Card/CardIcon.js";
import { cardTitle } from "assets/jss/material-dashboard-pro-react.js";
import CardHeader from "components/Card/CardHeader.js";
import { makeStyles, useTheme } from "@material-ui/core/styles";
import Heading from "components/Heading/Heading.js";
import Avatar from '@material-ui/core/Avatar'
import { useHistory } from "react-router-dom";
import moment from 'moment';
import ReactTable from "react-table";

async function getProfileDetail(id) {
    const response = await axios.get(`/api/playerstats/${id}`)
    return response.data
}
function filterCaseInsensitive(filter, row) {
	const id = filter.pivotId || filter.id;
	return (
		row[id] !== undefined ?
			String(row[id].toLowerCase()).includes(filter.value.toLowerCase())
		:
			true
	);
}
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
    },
    badge: {
        display: 'inline-block',
    },
    largeAvatar: {
        display: 'inline-block',
        height: '5rem',
        width: '5rem',
    }

};
const initialData = {
    total_matches: 0,
    total_matches_1650: 0,
    wins: 0,
    win_rate: 0,
    death_avg: 0,
    wins_1650: 0,
    win_rate_1650: 0,
    death_avg_1650: 0,
    first_bunker_cancels: 0,
    first_bunker_cancels_1650: 0,
    all_chats_per_game: 0,
}
const useStyles = makeStyles(styles);

export default function ProfileDetail(props) {
    const classes = useStyles()
    const [data, setData] = React.useState(initialData)
    const [loading, setLoading] = React.useState(true)
    const [matches, setMatches] = React.useState([])
    const history = useHistory()
    React.useEffect(() => {
        setLoading(true)
        const { id } = props.match.params
        getProfileDetail(id).then(res => {
            setData(res)
            setMatches(res.match_set)
            setLoading(false)
        })
    }, [])
    if (loading === true) { return <div>Loading...</div> }

    const addRowClick = (state, row) => {
        if (row && row.row) {
          const item = matches[row.index]
          return {
            onClick: (e) => {
              history.push(`/portal/matches/${item.id}`)
            }
          }
        }
        return {}
      }

    return (
        <div>
            <div className={classes.badge}>
            <Avatar className={classes.largeAvatar} src={data.avatar_url} >{data.name}</Avatar>
            <h1 className={classes.badge}>&nbsp; &nbsp;&nbsp;&nbsp;{data.name}</h1>
            </div>
            
            <Heading title="Overall" />
            <GridContainer>
                <GridItem>
                    <Card>
                        <CardHeader color="primary" icon>
                            <CardIcon color="danger">
                                TM
                            </CardIcon>
                           
                        </CardHeader>
                        <CardBody>
                        <h4 className={classes.cardIconTitle}>{data.total_matches}</h4>
                            <small>TOTAL MATCHES</small>
                        </CardBody>
                    </Card>
                </GridItem>

                <GridItem>
                    <Card>
                        <CardHeader color="primary" icon>
                            <CardIcon color="danger">
                                W
                            </CardIcon>
                       
                        </CardHeader>
                        <CardBody>
                        <h4 className={classes.cardIconTitle}>{data.wins}</h4>
                            <small>WINS</small>
                        </CardBody>
                    </Card>
                </GridItem>

                <GridItem>
                    <Card>
                        <CardHeader color="primary" icon>
                            <CardIcon color="danger">
                                WR
                            </CardIcon>
                           
                        </CardHeader>
                        <CardBody>
                        <h4 className={classes.cardIconTitle}>{data.win_rate.toFixed(1)}%</h4>
                            <small>WIN RATE</small>
                        </CardBody>
                    </Card>
                </GridItem>
                
                <GridItem>
                    <Card>
                        <CardHeader color="primary" icon>
                            <CardIcon color="danger">
                                PE
                            </CardIcon>
                            
                        </CardHeader>
                        <CardBody>
                        <h4 className={classes.cardIconTitle}>#{data.death_avg.toFixed(1)}</h4>
                            <small>AVG PLAYER ELIMINATED</small>
                        </CardBody>
                    </Card>
                </GridItem>
                <GridItem>
                    <Card>
                        <CardHeader color="primary" icon>
                            <CardIcon color="danger">
                                BC
                            </CardIcon>
                            
                        </CardHeader>
                        <CardBody>
                        <h4 className={classes.cardIconTitle}>{((data.first_bunker_cancels / data.total_matches)*100).toFixed(1)}%</h4>
                            <small>FIRST BUNKER CANCELLED</small>
                        </CardBody>
                    </Card>
                </GridItem>

                <GridItem>
                    <Card>
                        <CardHeader color="primary" icon>
                            <CardIcon color="danger">
                                BC
                            </CardIcon>
                            
                        </CardHeader>
                        <CardBody>
                        <h4 className={classes.cardIconTitle}>{data.all_chats_per_game.toFixed(1)}</h4>
                            <small># ALL-CHATS/GAME</small>
                        </CardBody>
                    </Card>
                </GridItem>
                
                

            </GridContainer>
            <Heading title="High ELO Lobbies (>=1650), Public Games Only" />


            <GridContainer>
                <GridItem>
                    <Card>
                        <CardHeader color="primary" icon>
                            <CardIcon color="danger">
                                TM
                            </CardIcon>
                           
                        </CardHeader>
                        <CardBody>
                        <h4 className={classes.cardIconTitle}>{data.total_matches_1650}</h4>
                            <small>TOTAL MATCHES</small>
                        </CardBody>
                    </Card>
                </GridItem>

                <GridItem>
                    <Card>
                        <CardHeader color="primary" icon>
                            <CardIcon color="danger">
                                W
                            </CardIcon>
                       
                        </CardHeader>
                        <CardBody>
                        <h4 className={classes.cardIconTitle}>{data.wins_1650}</h4>
                            <small>WINS</small>
                        </CardBody>
                    </Card>
                </GridItem>

                <GridItem>
                    <Card>
                        <CardHeader color="primary" icon>
                            <CardIcon color="danger">
                                WR
                            </CardIcon>
                           
                        </CardHeader>
                        <CardBody>
                        <h4 className={classes.cardIconTitle}>{data.win_rate_1650.toFixed(1)}%</h4>
                            <small>WIN RATE</small>
                        </CardBody>
                    </Card>
                </GridItem>
                
                <GridItem>
                    <Card>
                        <CardHeader color="primary" icon>
                            <CardIcon color="danger">
                                PE
                            </CardIcon>
                            
                        </CardHeader>
                        <CardBody>
                        <h4 className={classes.cardIconTitle}>#{data.death_avg_1650.toFixed(1)}</h4>
                            <small>AVG PLAYER ELIMINATED</small>
                        </CardBody>
                    </Card>
                </GridItem>

                <GridItem>
                    <Card>
                        <CardHeader color="primary" icon>
                            <CardIcon color="danger">
                                BC
                            </CardIcon>
                            
                        </CardHeader>
                        <CardBody>
                        <h4 className={classes.cardIconTitle}>{((data.first_bunker_cancels_1650 / data.total_matches_1650)*100).toFixed(1)}%</h4>
                            <small>FIRST BUNKER CANCELLED</small>
                        </CardBody>
                    </Card>
                </GridItem>
                

            </GridContainer>
            <GridContainer xs={12} md={12}>
            <GridItem  xs={12} md={12}>
                    <Card>
                        <CardHeader color="primary" icon>
                            <CardIcon color="danger">
                                Matches
                            </CardIcon>
                            
                        </CardHeader>
                        <CardBody>
                        <ReactTable
              data={data.match_set}
              filterable
              defaultFilterMethod={filterCaseInsensitive}
              columns={[
                {
                    Header: "Date",
                    id: "match_date",
                    accessor: d => {
                        return moment(d.match_date).format("YYYY-MM-DD hh:mm")
                    }
                },
                {
                  
                  Header: "Players",
                  accessor: "players"
                },
                {
                  Header: "Winners",
                  accessor: "winners"
                },
                
              ]}
              getTrProps={(state, rowInfo) => addRowClick(state, rowInfo)}
              defaultPageSize={10}
              showPaginationTop
              showPaginationBottom={false}
              className="-striped -highlight"
            />


                        </CardBody>
                    </Card>
                </GridItem>

            </GridContainer>
           
        </div>
    )
}
