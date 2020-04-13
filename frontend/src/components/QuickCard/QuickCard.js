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
const customStyles = {
    cardIconTitle: {
      ...cardTitle,
      marginTop: "15px",
      marginBottom: "0px"
    },
    iconColor: "danger",
    headerColor: "primary",
  };

const useStyles = makeStyles({...styles, customStyles});



export default function QuickCard(props) {
    for (const p in props) {
        if (props.hasOwnProperty(p)) {
            styles[p] = props[p]
        }
    }
    const classes = useStyles()
    const iconColor = props.iconColor == undefined ? "success" : props.iconColor
    const icon = props.icon == undefined ? <InfoIcon /> : props.icon
    const title = props.title == undefined ? "Information" : props.title
    
    return (
       
        <Card>
        <CardHeader color="success" icon>
        <CardIcon color={iconColor}>
            {icon}
          </CardIcon>
      
          
             <GridContainer>
                <GridItem style={{display: 'inline-flex'}}><Avatar>R</Avatar><Avatar>E</Avatar></GridItem>    
                <GridItem><h4 className={classes.cardIconTitle}>{title}    </h4></GridItem> 
            </GridContainer> 
        
      
        </CardHeader>
        <CardBody>
          {props.children}
        </CardBody>
  
      </Card>
      
    )
}
