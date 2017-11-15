import React from 'react';
import ReactDOM from 'react-dom';
import 'bootstrap/dist/css/bootstrap.css';

import './index.css';
import App from './components/App';
import registerServiceWorker from './registerServiceWorker';

const app = React.createFactory(App);

function start() {
  ReactDOM.render(app(), document.getElementById('root'));
  registerServiceWorker();
}

start();
