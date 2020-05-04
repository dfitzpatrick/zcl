import React from "react";
// react component for creating dynamic tables
import ReactTable from "react-table";

// @material-ui/core components
import { makeStyles } from "@material-ui/core/styles";
// @material-ui/icons
import Dvr from "@material-ui/icons/Dvr";
import Favorite from "@material-ui/icons/Favorite";
import Close from "@material-ui/icons/Close";
// core components
import GridContainer from "components/Grid/GridContainer.js";
import GridItem from "components/Grid/GridItem.js";
import Button from "components/CustomButtons/Button.js";
import Card from "components/Card/Card.js";
import CardBody from "components/Card/CardBody.js";
import CardIcon from "components/Card/CardIcon.js";
import CardHeader from "components/Card/CardHeader.js";
import CustomDropdown from "components/CustomDropdown/CustomDropdown"
import { useHistory } from "react-router-dom";

import {goodTimeDiff} from "../../helpers/dates"

import { cardTitle } from "assets/jss/material-dashboard-pro-react.js";
import axios from "axios";
import { createImportSpecifier } from "typescript";

const styles = {
  cardIconTitle: {
    ...cardTitle,
    marginTop: "15px",
    marginBottom: "0px"
  }
};

async function getLeaderboards(mode) {

    const response = await axios.get(`/api/leaderboards/?mode=${mode}`)
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
    const history = useHistory()
    const [lbData, setLbData] = React.useState([])
    const [mode, setMode] = React.useState("2v2v2v2")
    const [loading, setLoading] = React.useState(true)
    React.useEffect(() => {
        setLoading(true)
        getLeaderboards(mode).then(data => {
            setLbData(data)
            setLoading(false)
        })
    }, [])
    const [data, setData] = React.useState(
    lbData.map((prop, key) => {
      return {
        id: prop.id,
        name: prop.profile.name,
        position: prop.wins,
        office: prop.losses,
        age: prop.elo,
        actions: (
          // we've added some custom button actions
          <div className="actions-right">
            {/* use this button to add a like kind of action */}
            <Button
              justIcon
              round
              simple
              onClick={() => {
                let obj = data.find(o => o.id === key);
                alert(
                  "You've clicked LIKE button on \n{ \nName: " +
                    obj.name +
                    ", \nposition: " +
                    obj.position +
                    ", \noffice: " +
                    obj.office +
                    ", \nage: " +
                    obj.age +
                    "\n}."
                );
              }}
              color="info"
              className="like"
            >
              <Favorite />
            </Button>{" "}
            {/* use this button to add a edit kind of action */}
            <Button
              justIcon
              round
              simple
              onClick={() => {
                let obj = data.find(o => o.id === key);
                alert(
                  "You've clicked EDIT button on \n{ \nName: " +
                    obj.name +
                    ", \nposition: " +
                    obj.position +
                    ", \noffice: " +
                    obj.office +
                    ", \nage: " +
                    obj.age +
                    "\n}."
                );
              }}
              color="warning"
              className="edit"
            >
              <Dvr />
            </Button>{" "}
            {/* use this button to remove the data row */}
            <Button
              justIcon
              round
              simple
              onClick={() => {
                var newData = data;
                newData.find((o, i) => {
                  if (o.id === key) {
                    // here you should add some custom code so you can delete the data
                    // from this component and from your server as well
                    newData.splice(i, 1);
                    return true;
                  }
                  return false;
                });
                setData([...newData]);
              }}
              color="danger"
              className="remove"
            >
              <Close />
            </Button>{" "}
          </div>
        )
      };
    })
  );
  const classes = useStyles();
  const handleModeChoice = (value) => {
    setMode(value)
    setLoading(true)
    getLeaderboards(value).then(data => {
      setLbData(data)
      setLoading(false)
    })

  }
  const addRowClick = (state, row) => {
    if (row && row.row) {
      const item = lbData[row.index]
      return {
        onClick: (e) => {
          const target = `/portal/profile/${item.profile.id}`
          history.push(target)
        }
      }
    }
    return {}
  }
  return (<>
    <CustomDropdown
    onClick={handleModeChoice}
    buttonText={mode}
    dropdownList={[
      "2v2v2v2",
      "3v3v3v3",
      "1v1v1v1",
      "1v1",
      "2v2",
    ]}
    buttonProps={{color: "primary"}}
   />
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
              loading={loading}
              defaultFilterMethod={filterCaseInsensitive}
              columns={[
                {
                  
                  Header: "Rank",
                  accessor: "rank"
                },
                {
                  Header: "Name",
                  accessor: "profile.name"
                },
                {
                    Header: "ELO",
                    id: "elo",
                    accessor: d => Math.round(d.elo)
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
                {
                    Header: "Updated",
                    id: "updated",
                    accessor: d => {
                        return goodTimeDiff({
                            to: d.updated,
                            suffix: "ago"
                        })
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
  </>);
}
