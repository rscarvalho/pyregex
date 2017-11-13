import App from '../App';
import NavBar from '../NavBar';
import React from 'react';
import { shallow } from 'enzyme';

describe('components/App', () => {
  it('renders the NavBar', () => {
    const wrapper = shallow(<App />);

    expect(wrapper.find(NavBar)).toHaveLength(1);
  });
});
