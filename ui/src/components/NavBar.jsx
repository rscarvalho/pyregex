import MenuItem from 'react-bootstrap/lib/MenuItem';
import Nav from 'react-bootstrap/lib/Nav';
import NavDropdown from 'react-bootstrap/lib/NavDropdown';
import NavItem from 'react-bootstrap/lib/NavItem';
import Navbar from 'react-bootstrap/lib/Navbar';
import React from 'react';

export default function NavBar() {
  return (
    <Navbar inverse collapseOnSelect fixedTop>
      <Navbar.Header>
        <Navbar.Brand>
          <a href="/">
            <span className="logo">.*</span> PyRegex
          </a>
        </Navbar.Brand>
        <Navbar.Toggle />
      </Navbar.Header>
      <Navbar.Collapse>
        <Nav>
          <NavItem eventKey="home" href="#">
            Home
          </NavItem>
          <NavItem eventKey="changelog" href="#">
            Changelog
          </NavItem>
          <NavDropdown eventKey="help" title="Help" id="topnav-dropdown-help">
            <MenuItem eventKey="help-documentation">Official Python Documentation</MenuItem>
          </NavDropdown>
          <NavDropdown eventKey="contribute" title="Contribute" id="topnav-dropdown-contribute">
            <MenuItem eventKey="contribute-develop">Develop</MenuItem>
            <MenuItem eventKey="contribute-donate">Donate</MenuItem>
          </NavDropdown>
        </Nav>
      </Navbar.Collapse>
    </Navbar>
  );
}
