import React from "react";

// @material-ui/core components
import { makeStyles} from "@material-ui/core/styles";
// @material-ui/icons
import Group from "@material-ui/icons/Group";
// import LockOutline from "@material-ui/icons/LockOutline";
// core components
import GridContainer from "components/Grid/GridContainer.js";
import GridItem from "components/Grid/GridItem.js";
import Button from "components/CustomButtons/Button.js";
import InfoArea from "components/InfoArea/InfoArea.js";
import Card from "components/Card/Card.js";
import CardBody from "components/Card/CardBody.js";
import CastIcon from '@material-ui/icons/Cast';


import styles from "assets/jss/material-dashboard-pro-react/views/registerPageStyle";

const useStyles = makeStyles(styles);

export default function Home() {
  const [checked, setChecked] = React.useState([]);
  const handleToggle = value => {
    const currentIndex = checked.indexOf(value);
    const newChecked = [...checked];

    if (currentIndex === -1) {
      newChecked.push(value);
    } else {
      newChecked.splice(currentIndex, 1);
    }
    setChecked(newChecked);
  };
  const classes = useStyles();
  return (
    <div className={classes.container}>
      <GridContainer justify="center">
        <GridItem xs={12} sm={12} md={6}>
          <h2 className={classes.title}>Everything Zone Control, All Day</h2>
          <h5 className={classes.description}>
            We are a group of dedicated gamers that strive to build a fun interactive community
          </h5>
        </GridItem>
      </GridContainer>
      <GridContainer justify="center">
        <GridItem xs={12} sm={12} md={10}>
          <Card className={classes.cardSignup}>
            <h2 className={classes.cardTitle}>A discord-based community</h2>
            <CardBody>
              <GridContainer justify="center">
                <GridItem xs={12} sm={12} md={5}>
                  <InfoArea
                    title="Casted Weekly Tournaments"
                    description="Hosted tournaments every week in a bracket environment. Compete for a prize pool or bragging rights."
                    icon={CastIcon}
                    iconColor="rose"
                  />
                  <InfoArea
                    title="Casted Weekly League Play"
                    description="Arranged matches and seasons by Skill. Play equally-skilled lobbies with our Professional and Intermediate Leagues"
                    icon={CastIcon}
                    iconColor="primary"
                  />
                  <InfoArea
                    title="Coaching"
                    description="Want to improve your skills? Pair up with an experienced player and hone your craft."
                    icon={Group}
                    iconColor="info"
                  />
                </GridItem>
                <GridItem xs={12} sm={8} md={5}>
                  

  
          <h3>Ready to Play?</h3>
          <Button href="/portal" color="primary">Login w/ Discord</Button>



                </GridItem>
              </GridContainer>
            </CardBody>
          </Card>
        </GridItem>
      </GridContainer>
    </div>
  );
}
