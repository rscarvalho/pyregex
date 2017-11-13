import Col from 'react-bootstrap/lib/Col';
import Grid from 'react-bootstrap/lib/Grid';
import NavBar from './NavBar';
import React from 'react';
import Row from 'react-bootstrap/lib/Row';

export default function App() {
  return (
    <div className="app">
      <NavBar />
      <Grid fluid>
        <Row>
          <Col size={12}>The rest of the app goes here</Col>
        </Row>
      </Grid>
    </div>
  );
}
