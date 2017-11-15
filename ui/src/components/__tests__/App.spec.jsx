import { shallow } from 'enzyme';
import React from 'react';
import App from '../App';
import NavBar from '../NavBar';

describe('components/App', () => {
  it('renders the NavBar', () => {
    const wrapper = shallow(<App />);

    expect(wrapper.find(NavBar)).toHaveLength(1);
  });
});
