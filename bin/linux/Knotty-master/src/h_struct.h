#ifndef H_STRUCT_H_
#define H_STRUCT_H_

#include "structs.h"
#include <vector>
#include <string>
#include <array>
#include <algorithm>

// another way to represent a structure. Used to measure free energy of a give structure etc.
typedef struct h_str_features
{
    short int pair;
    char type;                   // type can be 'H', 'S', 'I', 'M' etc
    short int num_branches;
    int bri[MAX_BRANCHES];      // the i of each branch
    int arc;					// keeps the left base pair of the arc
    h_str_features()
    {
        pair = -1;
        type = NONE;
        num_branches = 0;
        arc = -1;
    }
} h_str_features;


// Hosna Feb 18, 2014
// I need a structure to hold the bracket type to be used in the strcture stack.
typedef struct brack_type
	{
		char open;
		char close;
		void copy(brack_type *other){
			open = other->open;
			close = other->close;
		}
		brack_type(char _open, char _close):
        open(_open),
        close(_close)
        {

        }
	}brack_type;


// Hosna, Feb 18 2014
// I need a stack to hold different types of brackets for structure formation
typedef struct brack_stack
{
	brack_type elem[5]; // Hosna, Feb 18, 2014 I don't see more than 5 different types of brackets being used in knotty
	int top;
} brack_stack;


// Hosna Feb 19, 2014
// I need a structure to hold the band type to be used in band array.
typedef struct band_elem
{
	band_elem *next;
	char open;
	char close;
	int outer_start;
	int outer_end;
	int inner_start;
	int inner_end;
	void copy(band_elem *other){
		other->outer_end = outer_end;
		other->outer_start = outer_start;
		other->inner_end = inner_end;
		other->inner_start = inner_start;
		other->open = open;
		other->close = close;
	}
	band_elem(char _open,char _close,int _outer_start, int _outer_end, int _inner_start, int _inner_end):
    open(_open),
    close(_close),
    outer_start(_outer_start),
    outer_end(_outer_end),
    inner_start(_inner_start),
    inner_end(_inner_end)
    {

    }
}band_elem;

static constexpr std::array<std::pair<char,char>, 4> brackets = {{
    {'(', ')'},
    {'[', ']'},
    {'{', '}'},
    {'<', '>'},
}};

struct Band {
    int i, j;
    int  color;
	Band(int i, int j, int color): i(i), j(j), color(color){
	}
};

inline bool crosses(int i, int j, int k, int l) {
    return (i < k && k < j && j < l) || (k < i && i < l && l < j);
}

// This is a graph coloring problem in essence
inline void fill_structure(minimum_fold *fres,std::string &structure) {
	int n = structure.length();
    std::vector<Band> bands;
	for (int i = 0; i < n; ++i) {
        if (fres[i].pair != -2 && i < fres[i].pair){
			bands.emplace_back(i, fres[i].pair, -1);
		}
    }
	// Sort by descending span as those with larger spans are more likely to cross things, but still not guaranteed
    auto by_span_descending = [](const Band &a, const Band &b) {
    int span_a = a.j - a.i, span_b = b.j - b.i;
    if (span_a != span_b) return span_a > span_b;
    return a.i < b.i;
    };
    std::sort(bands.begin(), bands.end(), by_span_descending);
	for(int i = 0; i<(int) bands.size();++i){
		std::vector<int> cross = {0,0,0};
		for(int j=0; j<i;++j){
			if(crosses(bands[i].i,bands[i].j,bands[j].i,bands[j].j)){
				cross[bands[j].color] = 1; // Can just reassign 1 if it crosses. Better than an if else as branches can be expensive
			}
		}
		// The order here should ensure that it picks correctly. cross[color] ensures we stop at the first 0 in the cross array
		int color = 0;
        while (color < (int)cross.size() && cross[color]) color++;
        bands[i].color = color;
	}
    for (int i = 0; i < (int) bands.size(); ++i) {
		std::pair<char,char> br = brackets[bands[i].color];
		structure[bands[i].i] = br.first;
		structure[bands[i].j] = br.second;
    }
}

#endif /*H_STRUCT_H_*/
