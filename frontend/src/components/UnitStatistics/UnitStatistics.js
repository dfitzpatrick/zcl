import React from 'react'
import GridContainer from "components/Grid/GridContainer.js";
import GridItem from "components/Grid/GridItem.js";
import Card from "components/Card/Card.js";
import CardBody from "components/Card/CardBody.js";
import CardIcon from "components/Card/CardIcon.js";
import CardHeader from "components/Card/CardHeader.js";
import { makeStyles } from '@material-ui/core/styles';
import Select from '@material-ui/core/Select';
import MenuItem from '@material-ui/core/MenuItem';
import Table from "components/Table/Table.js";
import styles from "assets/jss/material-dashboard-pro-react/views/extendedTablesStyle.js";
import bunkerIcon from "assets/img/unitIcons/bunker.png"
import marineIcon from "assets/img/unitIcons/marine.png"
import mercRaudIcon from "assets/img/unitIcons/mercraud.png"
import mercBunkerIcon from "assets/img/unitIcons/mercbunker.png"
import mercReaperIcon from "assets/img/unitIcons/mercreap.png"
import raudIcon from "assets/img/unitIcons/raud.png"
import reaperIcon from "assets/img/unitIcons/reaper.png"
import scvIcon from "assets/img/unitIcons/scv.png"
import spectreIcon from "assets/img/unitIcons/spectre.png"
import tankIcon from "assets/img/unitIcons/tank.png"
import turretIcon from "assets/img/unitIcons/turret.png"
import mercMarineIcon from "assets/img/unitIcons/warpig.png"
import missingIcon from "assets/img/unitIcons/missing.png"
import vsIcon from "assets/img/unitIcons/vs.png"
import shieldTowerIcon from "assets/img/unitIcons/shieldtower.png"
import sensorTowerIcon from "assets/img/unitIcons/sensortower.png"
import supplyDepotIcon from "assets/img/unitIcons/supplydepot.png"



function buildBaseDropDown(data, callback, state, id) {
    console.log('received data')
    console.log(data)
    const menuItems = data.map(e => {
        return <MenuItem value={e.id}>{e.name}</MenuItem>
    })
    return (
        <Select
          labelId="demo-simple-select-label"
          id={id}
          value={state}
          onChange={callback}
          defaultValue="Choose Player"
        >
        {menuItems}

        </Select>
    )
}
const initialData = [{
    id: 'loading',
    name: 'Loading',
    data: [{
        id: 'loading',
        name: 'Loading',
        units: [],
    }]
}]

function getUnitDetails(unit) {
    const units = {
        Marine: {
            displayName: 'Marine',
            icon: marineIcon,
        },
        WarPig: {
            displayName: 'War Pig',
            icon: marineIcon,
        },
        Reaper: {
            displayName: 'Reaper',
            icon: reaperIcon,
        },
        Bunker: {
            displayName: 'Bunker',
            icon: bunkerIcon,
        },
        SiegeBreakerSieged: {
            displayName: 'Tank',
            icon: tankIcon,
        },
        SCV: {
            displayName: 'SCV',
            icon: scvIcon,
        },
        HammerSecurity: {
            displayName: 'Hammer Security',
            icon: mercRaudIcon,
        },
        MercReaper: {
            displayName: 'Death Head',
            icon: mercReaperIcon,
        },
        Marauder: {
            displayName: 'Marauder',
            icon: mercRaudIcon,
        },
        AutoTurret: {
            displayName: 'Turret',
            icon: turretIcon,
        },
        HiveMindEmulator: {
            displayName: 'Shield Tower',
            icon: shieldTowerIcon,
        },
        SensorTower: {
            displayName: 'Sensor Tower',
            icon: sensorTowerIcon,
        },
        SupplyDepot: {
            displayName: 'Supply Depot',
            icon: supplyDepotIcon,
        }

    }
    const item = units[unit]||{'displayName': unit, icon: missingIcon}
    return item
}


function getElementFromId(data, id) {
    for (const index in data) {
        if (data[index].hasOwnProperty('id')) {
            if (data[index].id === id) {
                return data[index]
            }
        }

    }
    return initialData
}

function byKey(seq, key) {

    const container = {}
    for (const o of seq) {
        container[o[key]] = o
    }
    return container
}

function findMirrorMatchup(data, playerId, opponentId) {
    for (const index in data) {
        if (data[index].hasOwnProperty('id')) {
            if (data[index].id === playerId) {
                for (const opponent of data[index].data) {
                    if (opponent.id == opponentId) {
                        return opponent
                    }
                }
            }
        }
    }
    return null
}

function makeUnitTable(opponentData, mirrorData) {
    if (mirrorData.units === []) {
        return [[]]
    } 
    

    if (opponentData.units === []) {
        return [[]]
    }
    const mirrorUnits = byKey(mirrorData.units, 'name')
    let result = opponentData.units.map(item => {
        const created = mirrorUnits[item.name].created
        const killedPercent = parseInt((item.killed / created)*100)
        const lostPercent = parseInt((item.lost / item.created)*100)
        const unit = getUnitDetails(item.name)
        return [
            <img src={unit.icon} />,
            <h3>{unit.displayName}</h3>,
            <h4>{item.created}</h4>,
            <h4>{item.killed}</h4>,
            <h4>{item.lost}</h4>,
            <h4>{isNaN(killedPercent) ? 0 : killedPercent}%</h4>,
            <h4>{isNaN(lostPercent) ? 0 : lostPercent}%</h4>,

        ]
        
    })
    return result  
}

const useStyles = makeStyles(styles);

export default function UnitStatistics(props) {
    const data = props.data == 'undefined' ? initialData : props.data
    //const [data, setData] = React.useState(initialData)
    const [player, setPlayer] = React.useState(initialData[0].id)
    const [playerData, setPlayerData] = React.useState(initialData[0])
    const [opponentData, setOpponentData] = React.useState(initialData[0].data[0])
    const [mirrorData, setMirrorData] = React.useState(initialData[0].data[0])

    const [opponent, setOpponent] = React.useState(initialData[0].data[0].id)


    const handlePlayerChange = (event) => {
        selectPlayer(event.target.value)
    }
    const selectPlayer = (id) => {
        const pd = getElementFromId(data, id)
        setPlayerData(pd)
        setPlayer(id)
    }
    const selectOpponent = (id) => {
        const od = getElementFromId(playerData.data, id)
        const mirror = findMirrorMatchup(data, od.id, playerData.id)
        setOpponentData(od)
        setOpponent(id)
        setMirrorData(mirror)

    }


    const handleOpponentChange = (event) => {
        selectOpponent(event.target.value)
    }
    return (
        <div>
            <Card>
            <CardHeader color="success" icon>
                <CardIcon color="primary" icon>
                    Units
                </CardIcon>
            </CardHeader>
            <CardBody>
            <GridContainer xs={12} sm={9} md={6}>
                <GridItem xs={4} sm={3} md={2}>
                {buildBaseDropDown(data, handlePlayerChange, player, "statsPlayer")}
                </GridItem>
                <GridItem xs={4} sm={3} md={2}>
                    <img src={vsIcon} alt="VERSUS" width="100" height="92" />
                </GridItem>
                <GridItem xs={4} sm={3} md={2}>
                {buildBaseDropDown(playerData.data, handleOpponentChange, opponent, "statsOpponent")}
                </GridItem>
            </GridContainer>
        
            <Table
                tableHead={["","Unit", "Created", "Killed","Lost", "K%", "L%"]}
                tableData={makeUnitTable(opponentData, mirrorData)}
            />
            </CardBody>
            </Card>
            
            


        
            
            Hello UnitStatistics
        </div>
    )
}
