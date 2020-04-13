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
import { useHistory } from "react-router-dom";
import axios from "axios";
import moment from 'moment';

const styles = {
  cardIconTitle: {
    ...cardTitle,
    marginTop: "15px",
    marginBottom: "0px"
  }
};

async function getMatches() {
    const response = await axios.get('/api/matches')
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

export default function ReactTables(props) {

    const [matches, setMatches] = React.useState([])
    const history = useHistory()

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
    
    React.useEffect(() => {
      getMatches().then(data => {
          setMatches(data)
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
            <h4 className={classes.cardIconTitle}>Matches</h4>
          </CardHeader>
          <CardBody>
            <ReactTable
              data={matches}
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
                {
                  Header: "League",
                  id: 'league',
                  accessor: d => {
                    if (d.league == null) {
                      return "Public"
                    } else {
                      return `${d.league.name} - ${d.season.name}`
                    }
                  }
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
  );
}
