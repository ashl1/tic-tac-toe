import React, { Component } from 'react';
import Cookies from 'js-cookie'
import uuidv1 from 'uuid'

import logo from './logo.svg';
import './App.css';

const TOKEN_COOKIE_NAME = 'tic-tac-toe-VVzlet-masterclass'
const WS_SERVER = 'ws://192.168.88.87:8080'
const WS_PATH = '/tic-tac-toe-VVzlet-masterclass'

class App extends Component {

  componentDidMount() {
    let token = Cookies.get(TOKEN_COOKIE_NAME)
    if (!token) {
      token = uuidv1()
      Cookies.set(TOKEN_COOKIE_NAME, token)
    }
    this.setState({token})

    const ws = new WebSocket(WS_SERVER + WS_PATH)
    this.setState({ws})
    ws.onopen = () => {
      console.log('WS Connected')
      ws.send(JSON.stringify({
        token,
        command: 'init',
        name: 'Noname' // FIXME:
      }))
      ws.send(JSON.stringify({
        token,
        command: 'get_clients'
      }))
    }
    ws.onmessage = (event) => {
      const d = JSON.parse(event.data)
      if (d['answer'] === 'clients') {
        console.log(d['data'])
        const clients = d['data']['ready_clients']
        if (clients.length > 0) {
          // FIXME: not here
          ws.send(JSON.stringify({
            token,
            command: 'want_play_with',
            alien_token: clients[0]['token'], // FIXME chosen token
          }))
        }
      } else if (d['answer'] === 'are_ready_to_play') {
        // FIXME: real check
        ws.send(JSON.stringify({
          token,
          command: 'ready_to_play'
        }))
      } else {
        console.log('Received other data: ')
        console.log(d)
      }
    }
    ws.onerror = (error) => {
      console.log('Error in WebSocket: ' + error.message)
    }
  }

  componentWillUnmount() {
    this.state.ws.close()
  }

  render() {
    return (
      <div className="App">
        <header className="App-header">
          <img src={logo} className="App-logo" alt="logo" />
          <h1 className="App-title">Welcome to React</h1>
        </header>
        <p className="App-intro">
          To get started, edit <code>src/App.js</code> and save to reload.
        </p>
      </div>
    );
  }
}

export default App;
