import React from 'react'
import Slider from '@material-ui/core/Slider'
import GridContainer from "components/Grid/GridContainer.js";
import GridItem from "components/Grid/GridItem.js";
import Card from "components/Card/Card.js";
import CardBody from "components/Card/CardBody.js";
import CardFooter from "components/Card/CardFooter.js";

import Paper from '@material-ui/core/Paper';
import { makeStyles } from '@material-ui/core/styles';
import Heading from 'components/Heading/Heading';

function getMaxLength(d) {
    let x = d
    // For the slider to know what the max range is
    const result = Math.max(...x.map(e => e.length))
    return isNaN(result) ? 1 : result - 1
}


function makeUpgradeArraySameLength(data) {
    let targetLength = getMaxLength(data)
    for (const index in data) {
        let extra = targetLength - data[index].length
        let lastRecord = data[index].slice(-1)[0]
        for (let i = 0; i <= extra; i++) {
            data[index].push(lastRecord)
        }
    }
    return data
}

function getUpgradeValue(player) {
    const sumUp = (n) => [...Array(n).keys()].map(v => (v + 1) * 25).reduce((a, b) => a + b, 0)
    return (
        sumUp(player.MarineArmor) +
        sumUp(player.MarineWeapons) +
        sumUp(player.MarineAttackRange) +
        sumUp(player.MarineLifeRegeneration) +
        sumUp(player.MarineMovespeed)
    )
}


export default function UpgradeViewer(props) {
    const data = props.data == undefined ? [] : makeUpgradeArraySameLength(props.data)
    const [sliderIndex, setSliderIndex] = React.useState(0)
    const onSliderChange = (e, v) => {
        setSliderIndex(v)
    }
    const upgradesChanged = (data, index) => {
        if (index == 0) {
            return false
        }
        let current = data[index]
        let previous = data[index - 1]
        if (getUpgradeValue(current) - getUpgradeValue(previous) > 0) {
            return "icon"
        } else {
            return ""
        }
    }
    return (
        <div>
            <GridContainer xs={12} sm={12} md={12}> 
                <GridItem>
                    <Heading
                    title="Upgrades"
                    />
                    <h4>Use the slider to see the upgrade progression.</h4>
                </GridItem>
                <GridItem xs={11} sm={11} md={11}>
                    <div id="sliderUpgradeSequence" className="slider-primary"/>
                    <Slider
                        onChange={onSliderChange}
                        max={getMaxLength(data)}
                        style={{margin: '30px 30px 30px 30px'}}
                    />

                </GridItem>
            </GridContainer>

            <GridContainer>
                {data.map(e => (

                    <GridItem xs={12} sm={6} md={3}>
                        <Card>
                            <CardBody>

                                <h3>{e[sliderIndex].name} ${getUpgradeValue(e[sliderIndex])}</h3>
                                <hr />
                                <GridContainer>
                                    <GridItem>
                                        <Paper>
                                            ARMOR
                                            <h3>{e[sliderIndex].MarineArmor}</h3>
                                        </Paper>
                                    </GridItem>
                                    <GridItem>
                                        <Paper>
                                            ATTACK
                                            <h3>{e[sliderIndex].MarineWeapons}</h3>
                                        </Paper>
                                    </GridItem>
                                    <GridItem>
                                        <Paper>
                                            RANGE
                                            <h3>{e[sliderIndex].MarineAttackRange}</h3>
                                        </Paper>
                                    </GridItem>
                                    <GridItem>
                                        <Paper>
                                            REGEN
                                            <h3>{e[sliderIndex].MarineLifeRegeneration}</h3>
                                        </Paper>
                                    </GridItem>
                                    <GridItem>
                                        <Paper>
                                            SPEED
                                            <h3>{e[sliderIndex].MarineMovespeed}</h3>
                                        </Paper>
                                    </GridItem>
                                </GridContainer>


                            </CardBody>
                            <CardFooter>
                                TS: {e[sliderIndex].total_score} | GT: {e[sliderIndex].game_time}
                            </CardFooter>

                        </Card>



                    </GridItem>


                ))}
            </GridContainer>
        </div>
    )
}
