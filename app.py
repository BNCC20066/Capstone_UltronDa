from flask import Flask, render_template
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64

app = Flask(__name__)

playstore = pd.read_csv('data/googleplaystore.csv')

playstore.drop_duplicates(subset=['App'], keep= 'first')

# bagian ini untuk menghapus row 10472 karena nilai data tersebut tidak tersimpan pada kolom yang benar
playstore.drop([10472], inplace=True)

playstore[['Category','Type','Content Rating','Android Ver']]= playstore[['Category','Type','Content Rating','Android Ver']].astype('category')

playstore.Installs = playstore['Installs'].apply(lambda x: x.replace(',',''))
playstore.Installs = playstore['Installs'].apply(lambda x: x.replace('+',''))


# Bagian ini untuk merapikan kolom Size, Anda tidak perlu mengubah apapun di bagian ini
playstore['Size'].replace('Varies with device', np.nan, inplace = True ) 
playstore.Size = (playstore.Size.replace(r'[kM]+$', '', regex=True).astype(float) * \
             playstore.Size.str.extract(r'[\d\.]+([kM]+)', expand=False)
            .fillna(1)
            .replace(['k','M'], [10**3, 10**6]).astype(int))
playstore['Size'].fillna(playstore.groupby('Category')['Size'].transform('mean'),inplace = True)

playstore.Price = playstore['Price'].apply(lambda x: x.replace('$',''))
playstore['Price']= playstore['Price'].astype("float")

# Ubah tipe data Reviews, Size, Installs ke dalam tipe data integer
playstore[['Installs','Reviews','Size']]= playstore[['Installs','Reviews','Size']].astype('int64')

@app.route("/")
# This fuction for rendering the table
def index():
    df2 = playstore.copy()

    # Statistik
    top_category = pd.crosstab(index= df2['Category'], columns='Jumlah').sort_values(by='Jumlah', ascending= False)
    # Dictionary stats digunakan untuk menyimpan beberapa data yang digunakan untuk menampilkan nilai di value box dan tabel
    stats = {
        'most_categories' : top_category.iloc[0,0],
        'total' : top_category.iloc[0,0],
        'rev_table' : playstore[['Category','App','Reviews','Rating']].groupby(by=['Category','App']).agg({'Reviews':'sum','Rating':'mean'}).sort_values(by='Reviews', ascending=False).head(10).reset_index ().to_html(classes=['table thead-light table-striped table-bordered table-hover table-sm'])
    }

    ## Bar Plot
    cat_order = df2.groupby('Category',as_index=False).agg({
    'App' : 'count'}).rename({'Category':'Total'}, axis=1).sort_values(by='App',ascending=False).head()
    X = cat_order['Total'].values
    Y = cat_order['App'].values 
    my_colors = ["r","g","b","k","y","m","c"]
    # bagian ini digunakan untuk membuat kanvas/figure
    fig = plt.figure(figsize=(8,3),dpi=300)
    fig.add_subplot()
    # bagian ini digunakan untuk membuat bar plot
    plt.barh(X,Y, color=my_colors)
    plt.title('TOTAL APPS PER CATEGORY')
    # bagian ini digunakan untuk menyimpan plot dalam format image.png
    plt.savefig('cat_order.png',bbox_inches="tight") 
    
    # bagian ini digunakan untuk mengconvert matplotlib png ke base64 agar dapat ditampilkan ke template html
    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    # variabel result akan dimasukkan ke dalam parameter di fungsi render_template() agar dapat ditampilkan di 
    # halaman html
    result = str(figdata_png)[2:-1]
    
    ## Scatter Plot
    X = df2['Reviews'].values # axis x
    Y = df2['Rating'].values # axis y
    area = playstore['Installs'].values/10000000 # ukuran besar/kecilnya lingkaran scatter plot
    fig = plt.figure(figsize=(7,5))
    fig.add_subplot()
    # isi nama method untuk scatter plot, variabel x, dan variabel y
    plt.scatter(x=X,y=Y, s=area, alpha=0.3)
    plt.title("APPS' RELATIONSHIPS & DISTRIBUTIONS")
    plt.xlabel('Reviews')
    plt.xticks([0,5000000,10000000,15000000,20000000,25000000,30000000,35000000,40000000,45000000,50000000,55000000,60000000,65000000,70000000,75000000,80000000],
           ['0','5M','10M','15M','20M','25M','30M','35M','40M','45M','50M','55M','60M','65M','70M','75M','80M'],rotation=20)
    plt.yticks([1.,1.5,2.,2.5,3.,3.5,4.,4.5,5.])
    plt.ylabel('Rating')
    plt.savefig('rev_rat.png',bbox_inches="tight")

    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    result2 = str(figdata_png)[2:-1]

    ## Histogram Size Distribution
    X=(df2['Size']/1000000).values
    fig = plt.figure(figsize=(5,5))
    fig.add_subplot()
    plt.hist(X,bins=100, density=True,  alpha=0.75)
    plt.xlabel('Size')
    plt.ylabel('Frequency')
    plt.title('SIZE FREQ (MB)')
    plt.savefig('hist_size.png',bbox_inches="tight")

    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    result3 = str(figdata_png)[2:-1]

    ## Buatlah sebuah plot yang menampilkan insight di dalam data 
    plt.figure(figsize=(7,5))
    plt.title("Application User")
    circle = plt.Circle((0, 0, 0, 0, 0, 0), 0.5, color='white')
    g = plt.pie(df2['Content Rating'].value_counts(), 
    wedgeprops = { 'linewidth' : 2, 'edgecolor' : 'white' }, 
    labels=['Adults only 18+','Everyone','Everyone 10+','Mature 17+','Teen','Unrated'],
    colors=['skyblue','b','navajowhite','y','r','#B7C3F3'],autopct='%1.1f%%',
    explode=(0.025,0.025,0.025,0.025,0.025,0.025), rotatelabels=True)
    plt.legend()
    p = plt.gcf()
    p.gca().add_artist(circle)
    plt.show()
    plt.savefig('application_user.png',bbox_inches="tight")

    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    result4 = str(figdata_png)[2:-1]
    # Tambahkan hasil result plot pada fungsi render_template()
    return render_template('index.html', stats=stats, result=result, result2=result2, result3=result3, result4=result4)

if __name__ == "__main__": 
    app.run(debug=True)
