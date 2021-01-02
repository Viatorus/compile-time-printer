const path = require('path');
const { CleanWebpackPlugin } = require('clean-webpack-plugin');
const CopyPlugin = require('copy-webpack-plugin');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const TerserPlugin = require('terser-webpack-plugin');

module.exports = {
  mode: 'production',
  entry: {
    app: './src/js/index.js',
    'editor.worker': 'monaco-editor/esm/vs/editor/editor.worker.js'
    // "json.worker": 'monaco-editor/esm/vs/language/json/json.worker',
    // "css.worker": 'monaco-editor/esm/vs/language/css/css.worker',
    // "html.worker": 'monaco-editor/esm/vs/language/html/html.worker',
    // "ts.worker": 'monaco-editor/esm/vs/language/typescript/ts.worker',
  },
  resolve: {
    alias: {
      CSS: path.resolve(__dirname, 'src/css/'),
      CTP: path.resolve(__dirname, '../')
    }
  },
  output: {
    globalObject: 'self',
    filename: '[name].[contenthash].js',
    path: path.resolve(__dirname, 'dist'),
    publicPath: ''
  },
  module: {
    rules: [
      {
        test: /\.css$/,
        use: [MiniCssExtractPlugin.loader, 'css-loader']
      },
      {
        test: /\.scss$/,
        use: [MiniCssExtractPlugin.loader, 'css-loader', 'sass-loader']
      },
      {
        test: /\.(woff|woff2|eot|ttf|otf|svg)$/,
        use: ['file-loader']
      },
      {
        test: /\.([hc]pp|py)$/,
        use: ['raw-loader']
      }
    ]
  },
  optimization: {
    moduleIds: 'deterministic',
    runtimeChunk: 'single',
    splitChunks: {
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all'
        }
      }
    },
    minimize: true,
    minimizer: [new TerserPlugin()]
  },
  plugins: [
    new CleanWebpackPlugin(),
    new CopyPlugin({
      patterns: [
        { from: 'static', to: 'static' },
        { from: 'favicon', to: '.' }
      ],
      options: {
        concurrency: 100
      }
    }),
    new MiniCssExtractPlugin(),
    new HtmlWebpackPlugin({
      template: path.resolve(__dirname, 'src', 'index.html')
    })
  ],
  devServer: {
    writeToDisk: true
  }
};
