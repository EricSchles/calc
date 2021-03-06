/* global window */

/**
 * Implementation of a panel that can slide up and down if jQuery
 * is present on the page. If jQuery is not present, it gracefully
 * degrades to a panel without animation.
 */

import React from 'react';
import ReactTransitionGroup from 'react-addons-transition-group';

import { FirstChild } from './util';

class InnerSlideyPanel extends React.Component {
  componentWillEnter(cb) {
    this.props.$(this.el).hide().slideDown('fast', cb);
  }

  componentWillLeave(cb) {
    this.props.$(this.el).slideUp('fast', cb);
  }

  render() {
    const newProps = { ref: (el) => { this.el = el; } };

    Object.assign(newProps, this.props);

    delete newProps.children;
    delete newProps.component;
    delete newProps.$;

    return React.createElement(
      this.props.component,
      newProps,
      this.props.children,
    );
  }
}

InnerSlideyPanel.propTypes = {
  component: React.PropTypes.any,
  children: React.PropTypes.any.isRequired,
  $: React.PropTypes.func,
};

InnerSlideyPanel.defaultProps = {
  component: 'span',
  $: window.$ || function fakeJquery() {
    return {
      hide() { return this; },
      slideUp(speed, cb) { cb(); },
      slideDown(speed, cb) { cb(); },
    };
  },
};

export default function SlideyPanel(props) {
  let innerPanel = null;

  if (props.expanded) {
    const innerProps = Object.assign({}, props);

    delete innerProps.expanded;

    innerPanel = (
      <InnerSlideyPanel {...innerProps}>
        {props.children}
      </InnerSlideyPanel>
    );
  }

  return (
    <ReactTransitionGroup component={FirstChild}>
      {innerPanel}
    </ReactTransitionGroup>
  );
}

SlideyPanel.propTypes = Object.assign({}, InnerSlideyPanel.propTypes, {
  expanded: React.PropTypes.bool,
});

SlideyPanel.defaultProps = Object.assign({}, InnerSlideyPanel.defaultProps, {
  expanded: false,
});
