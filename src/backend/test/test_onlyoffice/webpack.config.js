const path = require('path');

module.exports = {
  mode: 'development',
  entry: './src/main.ts',
  module: {
    rules: [
      {
        test: /\.ts$/,
        use: 'ts-loader',
        exclude: /node_modules/,
      },
    ],
  },
  resolve: {
    extensions: ['.ts', '.js'],
  },
  output: {
    filename: 'bundle.js',
    path: path.resolve(__dirname, 'dist'),
    publicPath: '/', // 确保 publicPath 正确
  },
  devServer: {
    static: {
      directory: path.resolve(__dirname, 'src'), // 指定静态文件服务的目录
    },
    open: true,
    hot: true, // 启用热更新
    compress: true, // 启用 gzip 压缩
  },
};