import React from 'react'
import { makeStyles } from "@material-ui/core/styles";
import Card from "components/Card/Card.js";
import CardHeader from "components/Card/CardHeader.js";
import CardIcon from "components/Card/CardIcon.js";
import CardBody from "components/Card/CardBody.js";
import Avatar from '@material-ui/core/Avatar';
import GridContainer from "components/Grid/GridContainer.js";
import GridItem from "components/Grid/GridItem.js";
import Table from "components/Table/Table.js";


import styles from "assets/jss/material-dashboard-pro-react/views/dashboardStyle.js";
const useStyles = makeStyles(styles);


export default function MatchSummary(props) {
    const data = props.data === undefined ? [] : props.data
    const classes = useStyles();
    return (
        <>
          <Card>
            <CardHeader color="success" icon>
            <CardIcon color="success">
                RM
              </CardIcon>
              <h4 className={classes.cardIconTitle}>
                My Recent Matches
              </h4>
            </CardHeader>
            <CardBody>
              <GridContainer justify="space-between">
                <GridItem xs={12} sm={12} md={5}>
                  <Table
                    tableData={data.map(item => [
                      <Avatar>W</Avatar>, 
                      item.players,
                      item.winners,
                      ])}
                  />
                </GridItem>
                
              </GridContainer>
            </CardBody>
          </Card>
        </>
    )
}
