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
  const classes = useStyles();
  const history = useHistory()
  


    const [matches, setMatches] = React.useState([])
    const [pageSize, setPageSize] = React.useState(10)
    const [page, setPage] = React.useState(0)
    const [pages, setPages] = React.useState(null)
    const [loading, setLoading] = React.useState(true)


    const fetchMatches = (state, instance) => {
      setLoading(true)
      const url = `/api/matches/`
      const offset = state.page * state.pageSize
      const target = `${url}?limit=${state.pageSize}&offset=${offset}`
      axios.get(target).then(
        res => {
          const pages = Math.round(res.data.count / state.pageSize)
          console.log(res.data)
          setMatches(res.data.results)
          setPages(pages)
          setLoading(false)
        }
      )
    }

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
             manual
              data={matches}
              pages={pages}
              loading={loading}
              onFetchData={fetchMatches}
              defaultPageSize={pageSize}
             
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
