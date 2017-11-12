import './index.css';

import App from './components/App';
import React from 'react';
import ReactDOM from 'react-dom';
import registerServiceWorker from './registerServiceWorker';

function start() {
  ReactDOM.render(<App />, document.getElementById('root'));
  registerServiceWorker();
}

start();
