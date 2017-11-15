import { REGEX_FLAGS } from '../constants';

export default class RegexBuilder {
  constructor(rawData) {
    const data = (() => {
      if (typeof rawData === 'string') {
        const decoded = decodeURIComponent(atob(rawData));
        return JSON.parse(decoded);
      } else if (typeof rawData === 'object' && rawData !== null) {
        return rawData;
      }
      return {};
    })();

    this.flags = {};
    this.source = data.regex || null;
    this.testString = data.test_string || null;
    this.matchType = data.match_type || 'match';
    this.setFlags(data.flags);
  }

  get data() {
    return {
      regex: this.source,
      flags: this.getFlag(),
      match_type: this.matchType,
      test_string: this.testString,
    };
  }

  encodeData() {
    const json = JSON.stringify(this.data);
    encodeURIComponent(btoa(json));
  }

  setFlags(flags) {
    this.flags = Object.keys(REGEX_FLAGS)
      .map(key => [key, REGEX_FLAGS[key]])
      .reduce(
        (acc, [key, value]) => ({
          ...acc,
          [key]: false,
        }),
        {},
      );
  }

  getFlag() {}
}
