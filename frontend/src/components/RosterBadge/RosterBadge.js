import React from 'react'
import { useParams } from 'react-router-dom'
import GridContainer from "components/Grid/GridContainer.js";
import GridItem from "components/Grid/GridItem.js";
import Button from "components/CustomButtons/Button.js";
import Card from "components/Card/Card.js";
import CardBody from "components/Card/CardBody.js";
import CardIcon from "components/Card/CardIcon.js";
import CardHeader from "components/Card/CardHeader.js";
import CardFooter from "components/Card/CardFooter.js";
import { cardTitle } from "assets/jss/material-dashboard-pro-react.js";
import { makeStyles } from "@material-ui/core/styles";
import InfoIcon from '@material-ui/icons/Info';
import axios from "axios";
import moment from 'moment';
import CardAvatar from "components/Card/CardAvatar.js";
import styles from "assets/jss/material-dashboard-pro-react/views/dashboardStyle.js";
import avatar from "assets/img/faces/marc.jpg";
import Avatar from '@material-ui/core/Avatar'
import { teamData } from "variables/charts.js"
import { isNoSubstitutionTemplateLiteral } from 'typescript';

const customStyles = {
    cardIconTitle: {
        ...cardTitle,
        marginTop: "15px",
        marginBottom: "0px"
    },
    iconColor: "danger",
    headerColor: "primary",

    inputColor: {
        position: 'relative'
    }

};

function getPositionAbbreviation(n) {
    const positions = {
        0: 'TL',
        1: 'TR',
        2: 'BR',
        3: 'BL',
    }
    return positions[n.toString()]
}
function findLeaderboardById(data, id) {
    for (const lb of data) {
        if (lb.hasOwnProperty('profile')) {
            const profile = lb.profile
            if (profile.hasOwnProperty('id')) {
                if (profile.id == id) {
                    return lb
                }

            }
            
        }
    }
    return null
}
const initialData = {
    id: 0,
    rosters: [],
    created: "",
    updated: "",
    position: 0,
    outcome: "",
    match: 0,
    team: 0
}
const useStyles = makeStyles({ ...styles, customStyles });

export default function RosterBadge(props) {
    const lbData = props.leaderboardData == undefined ? [] : props.leaderboardData
    const classes = useStyles()
    const data = props.team == undefined ? initialData : props.team
    const iconColor = props.iconColor == undefined ? "success" : props.iconColor
    const icon = props.icon == undefined ? <InfoIcon /> : props.icon
    const title = props.title == undefined ? "Information" : props.title
    //const [leaderBoardData, setLeaderBoardData] = React.useState([])
    

    const lbStats = (id) => {
        const lb = findLeaderboardById(lbData, id)
        if (lb == null) {
            return <GridItem><h4>Not Currently Ranked</h4></GridItem>
            } else {
               return (<>
                <GridItem>#{lb.rank} <small>RANK</small></GridItem>
                <GridItem>{parseFloat(lb.elo).toFixed(0)} <small>ELO</small></GridItem>
                <GridItem>{lb.wins} <small>WINS</small></GridItem>
                <GridItem>{lb.losses} <small>LOSSES</small></GridItem>
                <GridItem>{lb.win_rate}% <small>WIN RATE</small></GridItem>
              </> ) 
            }
        }

    const trophyIcon = data.outcome == 'win' ? <i class="fas fa-trophy"></i> : ""
    const rosters = data.rosters.map(p => {
        const colorBlock = {
            backgroundColor: 'rgba(' + p.color + ')'
        }
        const lane = p.lane == null ? "No Lane" : "Laning " + p.lane.name
        return (<>
            <GridContainer>
                        <GridItem style={{ display: 'inline-flex' }}>
                            <Avatar src={p.sc2_profile.avatar_url}>{p.sc2_profile.name}</Avatar>
                        </GridItem>
                        <GridItem style={colorBlock}>
                            
                        </GridItem>
                        <GridItem>
                            <h4 className={classes.cardIconTitle}>{p.sc2_profile.name} </h4><small>({lane})</small>
                        </GridItem>
                        </GridContainer>
                        
                        <GridContainer>
                            {lbStats(p.sc2_profile.id)}
                        </GridContainer>
                    <hr />
        </>)
    })

    return (
        <div>
            <Card>
                <CardHeader icon>
                    <CardIcon color={data.outcome == 'win' ? 'success' : 'danger'}>
                        {getPositionAbbreviation(data.position)}
                        {trophyIcon}
                    </CardIcon>
                    <h3></h3>
                </CardHeader>
                <CardBody>
                    {rosters}
  
                </CardBody>

            </Card>
        </div>
    )
}
