
import CssBaseline from '@material-ui/core/CssBaseline';
import { createMuiTheme, ThemeProvider, responsiveFontSizes  } from "@material-ui/core/styles";
import React from 'react';
import ReactDOM from 'react-dom';
import App from './App';
import './index.css';
import * as serviceWorker from './serviceWorker';

const theme = responsiveFontSizes(createMuiTheme({
  palette: {
    type: 'dark',
    primary: {
      main: '#616161',
      light: '#a4a4a4',
      dark: '#494949'
    },
    secondary: {
      main: '#03a9f4',
      light: '#67daff',
      dark: '007ac1'

    }

  }
}))



ReactDOM.render(
  <React.StrictMode>
    <ThemeProvider theme={theme}>
    <CssBaseline />
      <App />
    </ThemeProvider>
  </React.StrictMode>,
  document.getElementById('root')
);

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: https://bit.ly/CRA-PWA
serviceWorker.unregister();
