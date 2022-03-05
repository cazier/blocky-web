const webpack = require('webpack');
const path = require('path');
const glob = require('glob');

const MiniCssExtractPlugin = require('mini-css-extract-plugin')
const PurgeCSSPlugin = require('purgecss-webpack-plugin')

const src = path.resolve(__dirname, 'src');
const static = path.resolve(src, 'static');

var config = {
  entry: path.resolve(static, './index.js'),
  output: {
    path: path.join(static, 'dist'),
    filename: 'bundle.js'
  },
  module: {
    rules: [{
      test: /\.scss$/,
      use: [
        MiniCssExtractPlugin.loader,
        {
          loader: 'css-loader'
        },
        {
          loader: 'sass-loader',
          options: {
            sourceMap: false,
          }
        }
      ]
    }]
  },
  plugins: [
    new MiniCssExtractPlugin({ filename: 'style.css' }),
    new PurgeCSSPlugin({
      paths: glob.sync(path.resolve(src, 'templates') + '/*.html.j2', { nodir: true }),
      safelist: ['is-active'],
    }),
  ],
}

module.exports = (env, argv) => {
  if (argv.mode === 'development') {
    config.watch = true;
    config.mode = 'development';
  } else {
    config.mode = 'production';
  };

  return config;
};
