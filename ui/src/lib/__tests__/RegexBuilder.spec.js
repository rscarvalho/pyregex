import { REGEX_FLAGS } from '../../constants';
import RegexBuilder from '../RegexBuilder';

describe('lib/RegexBuilder', () => {
  describe('initialization', () => {
    let builder;

    beforeEach(() => {
      builder = new RegexBuilder();
    });

    xit('should initialize re flags to false', () => {
      Object.keys(REGEX_FLAGS).forEach((k) => {
        expect(builder.flags[k]).toBe(false);
      });
    });

    it('should initialize matchType to "match"', () => {
      expect(builder.matchType).toEqual('match');
    });
  });

  xit('should calculate builder flags according to the Python API', () => {
    const builder = new RegexBuilder();
    builder.flags.I = true;
    expect(builder.getFlag()).toBe(2);

    builder.flags.L = true;
    expect(builder.getFlag()).toBe(6);

    builder.flags.I = false;
    expect(builder.getFlag()).toBe(4);

    builder.flags.X = true;
    expect(builder.getFlag()).toBe(68);
  });

  xit('should calculate builder flags according to an integer number', () => {
    const builder = new RegexBuilder();
    expect(builder.flags.I).toBe(false);
    builder.setFlags(2);
    expect(builder.flags.I).toBe(true);
    builder.setFlags(4);
    expect(builder.flags.I).toBe(false);
    expect(builder.flags.L).toBe(true);
  });

  xit('should generate form data to send to the API', () => {
    const builder = new RegexBuilder();
    builder.setFlags({ I: true, L: true, X: false });

    builder.source = '(\\w+)';
    builder.testString = 'Hello, World!';
    builder.matchType = 'search';

    const data = builder.data;

    expect(Object.keys(data)).toEqual(['regex', 'flags', 'match_type', 'test_string']);
    expect(data.regex).toBe('(\\w+)');
    expect(data.test_string).toBe('Hello, World!');
    expect(data.match_type).toBe('search');
    expect(data.flags).toBe(6);
  });

  xit('should generate a Base64-encoded value of the regex data', () => {
    const expected =
      'eyJyZWdleCI6IkhlbGxvLCAoXFx3KykhIiwiZmxhZ3MiOj' +
      'YsIm1hdGNoX3R5cGUiOiJtYXRjaCIsInRlc3Rfc3RyaW5n' +
      'IjoiSGVsbG8sIFdvcmxkISJ9';

    const builder = new RegexBuilder({
      source: 'Hello, (\\w+)!',
      testString: 'Hello, World!',
      matchType: 'match',
    });

    builder.setFlags(6);

    const data = builder.data;
    expect(data.flags).toBe(6);

    expect(builder.encodeData()).toEqual(expected);
  });

  xit('should parse a Base64-encoded string and reconstruct regex data', () => {
    const data =
      'eyJyZWdleCI6IkhlbGxvLCAoXFx3KykhIiwiZmxhZ3MiOj' +
      'YsIm1hdGNoX3R5cGUiOiJtYXRjaCIsInRlc3Rfc3RyaW5n' +
      'IjoiSGVsbG8sIFdvcmxkISJ9';

    const builder = new RegexBuilder(data);
    const parsed = builder.data;

    expect(parsed.flags).toBe(6);
    expect(parsed.regex).toBe('Hello, (\\w+)!');
    expect(parsed.match_type).toBe('match');
    expect(parsed.test_string).toBe('Hello, World!');
  });

  xit('should re-create the data from a previously encoded string', () => {
    let builder = new RegexBuilder({
      source: 'Hello, (\\w+)!',
      testString: 'Hello, World!',
      matchType: 'match',
    });

    builder.setFlags(6);

    const expected = builder.data;
    const encoded_data = builder.encodeData();

    builder = new RegexBuilder(encoded_data);
    expect(expected).toEqual(builder.data);
  });
});
