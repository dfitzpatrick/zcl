import React from "react";
// react component for creating dynamic tables
import ReactTable from "react-table";

// @material-ui/core components
import { makeStyles } from "@material-ui/core/styles";
// @material-ui/icons

// core components
import GridContainer from "components/Grid/GridContainer.js";
import GridItem from "components/Grid/GridItem.js";
import Card from "components/Card/Card.js";
import CardBody from "components/Card/CardBody.js";
import CardIcon from "components/Card/CardIcon.js";
import CardHeader from "components/Card/CardHeader.js";

import { cardTitle } from "assets/jss/material-dashboard-pro-react.js";
import axios from "axios";

const styles = {
  cardIconTitle: {
    ...cardTitle,
    marginTop: "15px",
    marginBottom: "0px"
  }
};

async function getLeaderboards() {
    const response = await axios.get('/api/teams')
    return response.data
}
function filterCaseInsensitive(filter, row) {
	const id = filter.pivotId || filter.id;
	return (
		row[id] !== undefined ?
			String(row[id].toLowerCase()).startsWith(filter.value.toLowerCase())
		:
			true
	);
}

const useStyles = makeStyles(styles);

export default function ReactTables() {
    const [lbData, setLbData] = React.useState([])
    React.useEffect(() => {
        getLeaderboards().then(data => {
            console.log("data received")
            console.log(data)
            setLbData(data)
        })
    }, [])

  const classes = useStyles();
  return (
    <GridContainer>
      <GridItem xs={12}>
        <Card>
          <CardHeader color="primary" icon>
            <CardIcon color="danger">
              LB
            </CardIcon>
            <h4 className={classes.cardIconTitle}>Public Leaderboard</h4>
          </CardHeader>
          <CardBody>
            <ReactTable
              data={lbData}
              filterable
              defaultFilterMethod={filterCaseInsensitive}
              columns={[
                {
                  Header: "Rank",
                  accessor: "rank"
                },
                {
                  Header: "Name",
                  accessor: "players"
                },
                {
                    Header: "ELO",
                    accessor: "team_elo",
                },
                {
                    Header: "Win %",
                    id: "win_rate",
                    accessor: d => d.win_rate + "%",
                },
                {
                  Header: "W",
                  accessor: "wins"
                },
                {
                  Header: "L",
                  accessor: "losses"
                },
              ]}
              defaultPageSize={10}
              showPaginationTop
              showPaginationBottom={false}
              className="-striped -highlight"
            />
          </CardBody>
        </Card>
      </GridItem>
    </GridContainer>
  );
}
